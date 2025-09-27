from PySide6 import QtCore
import irsdk
import threading
import time


def _argb_to_hex(val):
    """Converte valor ARGB do iRacing em #RRGGBB"""
    if isinstance(val, int):
        r = (val >> 16) & 0xFF
        g = (val >> 8) & 0xFF
        b = val & 0xFF
        return f"#{r:02x}{g:02x}{b:02x}"
    return "#333333"


class IRacingClient(QtCore.QObject):
    # Sinal Qt → dispara pacotes de dados na thread principal
    data_ready = QtCore.Signal(dict)

    def __init__(self, poll_interval=1.0):
        super().__init__()
        self.ir = irsdk.IRSDK()
        self.running = False
        self.poll_interval = poll_interval

    def start(self):
        print(">>> DEBUG IRacingClient.start()")
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def loop(self):
        print(">>> DEBUG loop iniciado")
        while self.running:
            if not self.ir.is_initialized:
                print(">>> DEBUG chamando ir.startup()")
                self.ir.startup()

            if self.ir.is_initialized and self.ir.is_connected:
                self.ir.freeze_var_buffer_latest()
                packet = {
                    "standings": self._get_standings(),
                    "session": self._get_session_info(),
                    "fuel": self._get_fuel(),
                    "car_lr": self._get_car_lr()
                }

                if self.running:
                    try:
                        self.data_ready.emit(packet)
                    except RuntimeError:
                        print("[IRacingClient] Tentou emitir após objeto destruído")
                        self.running = False
                        break

            time.sleep(self.poll_interval)

    # -------------------
    # Standings
    # -------------------
    def _get_standings(self):
        data = []
        try:
            drivers_info = self.ir['DriverInfo']
            if not drivers_info or 'Drivers' not in drivers_info:
                return []

            drivers = drivers_info['Drivers'] or []
            positions = self.ir['CarIdxPosition'] or []
            qual_pos = self.ir['CarIdxQualPosition'] or []
            gaps = self.ir['CarIdxF2Time'] or []
            last_laps = self.ir['CarIdxLastLapTime'] or []
            incidents = self.ir['CarIdxIncidentCount'] or []

            print(f">>> DEBUG Encontrados {len(drivers)} drivers")

            for idx, drv in enumerate(drivers):
                print(f"[DEBUG DRIVER] idx={idx} name={drv.get('UserName')} pos={positions[idx] if idx < len(positions) else '??'}")
                name = drv.get('UserName')
                if not name:
                    continue

                pos = positions[idx] if idx < len(positions) else 0
                if pos <= 0:
                    pos = idx + 1
                # piloto fora do grid

                grid = qual_pos[idx] if idx < len(qual_pos) else pos
                pos_gain = pos - grid if grid and pos > 0 else 0

                # gap p/ líder
                gap_val = gaps[idx] if idx < len(gaps) else -1
                if pos == 1:
                    gap = "Líder"
                elif isinstance(gap_val, (int, float)) and gap_val > 0:
                    gap = f"+{gap_val:.1f}s"
                else:
                    gap = "---"

                # última volta
                last_val = last_laps[idx] if idx < len(last_laps) else -1
                last = f"{last_val:.3f}" if isinstance(last_val, (int, float)) and last_val > 0 else "--"

                # incidentes
                inc_val = incidents[idx] if idx < len(incidents) else 0

                # licença
                lic_str = drv.get("LicString", "--")
                lic_color = _argb_to_hex(drv.get("LicColor"))

                # classe
                class_id = drv.get("CarClassID")
                class_color = _argb_to_hex(drv.get("CarClassColor"))

                # carro
                car_num = drv.get("CarNumberRaw", "--")
                car_logo = None
                if "CarPath" in drv:
                    car_logo = f"assets/cars/{drv['CarPath']}.png"  # precisa existir no disco
                    
                print(f"[DEBUG STANDINGS] pos={pos} driver={name} ir={drv.get('IRating')} last={last} gap={gap}")
                data.append({
                    "pos": pos,
                    "pos_gain": pos_gain,
                    "driver": name,
                    "car_number": car_num,
                    "car_logo": car_logo,
                    "license": lic_str,
                    "license_color": lic_color,
                    "class_id": class_id,
                    "class_color": class_color,
                    "irating": drv.get('IRating', 0),
                    "ir_delta": "",  # estimativa futura
                    "last_lap": last,
                    "gap": gap,
                    "incidents": inc_val,
                })

            # ordena pela posição
            data.sort(key=lambda d: d["pos"])
        except Exception as e:
            print("[IRacingClient] Erro standings:", e)
            print(">>> DEBUG STANDINGS DATA", data[:3])  # mostra só os 3 primeiros

        return data

    # -------------------
    # Session Info
    # -------------------
    def _get_session_info(self):
        try:
            session_info = self.ir['SessionInfo'] or {}
            weekend_info = self.ir['WeekendInfo'] or {}

            sof_general = 0
            class_sof = {}

            laps = 0
            if session_info and 'Sessions' in session_info:
                sessions = session_info['Sessions']
                if sessions and isinstance(sessions, list):
                    first_session = sessions[0]

                    # SOF geral
                    sof_general = first_session.get('StrengthOfField', 0)

                    # Voltas
                    laps = first_session.get('ResultsLapsComplete', 0)

                    # SOF por classe
                    results = first_session.get('ResultsPositions', [])
                    if results and isinstance(results, list):
                        for pos in results:
                            class_id = pos.get("CarClassID")
                            sof_val = pos.get("StrengthOfField")
                            if class_id and sof_val:
                                class_sof[class_id] = sof_val

            time_remain = self.ir['SessionTimeRemain'] or 0

            track_temp = 0
            if weekend_info and 'TrackSurfaceTemp' in weekend_info:
                raw_temp = weekend_info['TrackSurfaceTemp']
                if isinstance(raw_temp, str):
                    try:
                        track_temp = float(raw_temp.split()[0])
                    except:
                        track_temp = 0
                elif isinstance(raw_temp, (int, float)):
                    track_temp = raw_temp

            return {
                "sof": sof_general,
                "class_sof": class_sof,
                "time": f"{time_remain/60:.1f} min" if isinstance(time_remain, (int, float)) else "--",
                "laps": laps,
                "track_temp": f"{track_temp:.1f} °C" if isinstance(track_temp, (int, float)) else "--",
            }
        except Exception as e:
            print("[IRacingClient] Erro sessão:", e)
            return {}

    # -------------------
    # Fuel Info
    # -------------------
    def _get_fuel(self):
        try:
            level = self.ir['FuelLevel']
            cap = self.ir['FuelCapacity']
            use_per_lap = self.ir['FuelUsePerLap']
            laps_rem = 0

            if isinstance(level, (int, float)) and isinstance(use_per_lap, (int, float)) and use_per_lap > 0:
                laps_rem = int(level / use_per_lap)

            return {
                "level": float(level) if isinstance(level, (int, float)) else 0,
                "capacity": float(cap) if isinstance(cap, (int, float)) else 0,
                "use_per_lap": float(use_per_lap) if isinstance(use_per_lap, (int, float)) else 0,
                "laps": laps_rem
            }
        except Exception as e:
            print("[IRacingClient] Erro fuel:", e)
            return {}
        
    # -------------------
    # Car Left/Right
    # -------------------
    def _get_car_lr(self):
        try:
            if not self.ir.is_connected:
                return {"cars": []}

            # Acesso direto ao valor
            val = self.ir['CarLeftRight']
            print(f"[DEBUG CarLR] raw={val}")

            if val is None:
                return {"cars": []}

            cars = []
            if val == 1:  # left
                cars.append({"side": "left", "gap_m": 10})
            elif val == 2:  # right
                cars.append({"side": "right", "gap_m": 10})
            elif val == 3:  # both
                cars.append({"side": "both", "gap_m": 10})

            return {"cars": cars}
        except Exception as e:
            print("[IRacingClient] Erro car_lr:", e)
            return {"cars": []}
