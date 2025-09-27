from PySide6 import QtCore
import irsdk
import threading
import time


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
                    "fuel": self._get_fuel()
                }
                # envia o pacote com segurança para a thread Qt
                self.data_ready.emit(packet)

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
            gaps = self.ir['CarIdxF2Time'] or []
            last_laps = self.ir['CarIdxLastLapTime'] or []
            incidents = self.ir['CarIdxIncidentCount'] or []

            print(f">>> DEBUG Encontrados {len(drivers)} drivers")

            for idx, drv in enumerate(drivers):
                name = drv.get('UserName')
                if not name:
                    continue

                pos = positions[idx] if idx < len(positions) else 0
                if pos <= 0:
                    pos = idx + 1  # fallback: evita standings vazio

                gap_val = gaps[idx] if idx < len(gaps) else -1
                gap = f"+{gap_val:.1f}s" if isinstance(gap_val, (int, float)) and gap_val > 0 else "---"

                last_val = last_laps[idx] if idx < len(last_laps) else -1
                last = f"{last_val:.3f}" if isinstance(last_val, (int, float)) and last_val > 0 else "--"

                inc_val = incidents[idx] if idx < len(incidents) else 0

                data.append({
                    "pos": pos,
                    "driver": name,
                    "irating": drv.get('IRating', 0),
                    "last_lap": last,
                    "gap": gap,
                    "incidents": inc_val,
                })

            data.sort(key=lambda d: d["pos"])
        except Exception as e:
            print("[IRacingClient] Erro standings:", e)

        return data

    # -------------------
    # Session Info
    # -------------------
    def _get_session_info(self):
        try:
            session_info = self.ir['SessionInfo'] or {}
            weekend_info = self.ir['WeekendInfo'] or {}

            sof = 0
            laps = 0
            if session_info and 'Sessions' in session_info:
                sessions = session_info['Sessions']
                if sessions and isinstance(sessions, list):
                    sof = sessions[0].get('StrengthOfField', 0)
                    laps = sessions[0].get('ResultsLapsComplete', 0)

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
                "sof": sof,
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
