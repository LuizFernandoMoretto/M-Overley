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


def _format_lap_time(seconds):
    """Formata tempo de volta em mm:ss.mmm"""
    if not isinstance(seconds, (int, float)) or seconds <= 0:
        return "--"
    minutes = int(seconds // 60)
    sec = int(seconds % 60)
    millis = int((seconds * 1000) % 1000)
    return f"{minutes}:{sec:02d}.{millis:03d}"


class IRacingClient(QtCore.QObject):
    # sinais para o Qt
    data_ready = QtCore.Signal(dict)
    car_lr_changed = QtCore.Signal(dict)

    def __init__(self, poll_interval=0.5):
        super().__init__()
        self.ir = irsdk.IRSDK()
        self.running = False
        self.poll_interval = poll_interval
        self._last_car_lr = None

        # guarda posição inicial caso não haja qualificação
        self._starting_positions = {}

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def loop(self):
        while self.running:
            if not self.ir.is_initialized:
                self.ir.startup()

            if self.ir.is_initialized and self.ir.is_connected:
                self.ir.freeze_var_buffer_latest()

                packet = {
                    "standings": self._get_standings(),
                    "session": self._get_session_info(),
                    "fuel": self._get_fuel(),
                    "car_lr": self._get_car_lr(),
                }

                try:
                    self.data_ready.emit(packet)
                except RuntimeError:
                    self.running = False
                    break

                if packet["car_lr"] != self._last_car_lr:
                    self._last_car_lr = packet["car_lr"]
                    try:
                        self.car_lr_changed.emit(packet["car_lr"])
                    except RuntimeError:
                        self.running = False
                        break

            time.sleep(self.poll_interval)

    # -------------------
    # Standings
    # -------------------
    def _get_standings(self):
        data = []
        try:
            drivers_info = self.ir["DriverInfo"]
            if not drivers_info or "Drivers" not in drivers_info:
                return []

            drivers = drivers_info["Drivers"] or []
            positions = self.ir["CarIdxPosition"] or []
            qual_pos = self.ir["CarIdxQualPosition"] or []
            last_laps = self.ir["CarIdxLastLapTime"] or []
            incidents = self.ir["CarIdxIncidentCount"] or []
            lap_dist_pct = self.ir["CarIdxLapDistPct"] or []
            session_time = self.ir["SessionTime"] or 0.0

            # identifica índice do líder
            leader_idx = None
            if positions:
                try:
                    leader_idx = positions.index(1)
                except ValueError:
                    leader_idx = None

            for drv in drivers:
                name = drv.get("UserName")
                car_idx = drv.get("CarIdx")
                if name is None or car_idx is None:
                    continue

                # posição atual
                pos = positions[car_idx] if car_idx < len(positions) else 0
                if pos <= 0:
                    pos = car_idx + 1  # fallback

                # grid inicial
                grid = None
                if "StartingGridPosition" in drv and drv["StartingGridPosition"] > 0:
                    grid = drv["StartingGridPosition"]
                elif car_idx < len(qual_pos) and qual_pos[car_idx] > 0:
                    grid = qual_pos[car_idx]
                elif "QualPosition" in drv and drv["QualPosition"] > 0:
                    grid = drv["QualPosition"]
                elif car_idx in self._starting_positions:
                    grid = self._starting_positions[car_idx]
                else:
                    self._starting_positions[car_idx] = pos
                    grid = pos

                # calcula delta
                if grid and grid > 0 and pos > 0:
                    pos_gain = grid - pos
                else:
                    pos_gain = 0

                # gap em tempo real
                gap = "---"
                if (
                    leader_idx is not None
                    and car_idx < len(lap_dist_pct)
                    and leader_idx < len(lap_dist_pct)
                ):
                    leader_pct = lap_dist_pct[leader_idx]
                    my_pct = lap_dist_pct[car_idx]

                    leader_pos = positions[leader_idx] if leader_idx < len(positions) else 0
                    my_pos = positions[car_idx] if car_idx < len(positions) else 0
                    lap_diff = leader_pos - my_pos

                    if pos == 1:
                        gap = "Líder"
                    elif lap_diff > 0:
                        gap = f"+{lap_diff} volta{'s' if lap_diff > 1 else ''}"
                    else:
                        leader_time = session_time - (1 - leader_pct) * (last_laps[leader_idx] or 0)
                        my_time = session_time - (1 - my_pct) * (last_laps[car_idx] or 0)
                        if leader_time and my_time:
                            diff = my_time - leader_time
                            gap = f"+{diff:.1f}s"

                # última volta
                last_val = last_laps[car_idx] if car_idx < len(last_laps) else -1
                last = _format_lap_time(last_val)

                # incidentes
                inc_val = incidents[car_idx] if car_idx < len(incidents) else 0

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
                    car_logo = f"assets/cars/{drv['CarPath']}.png"

                # país
                country = drv.get("Country") or drv.get("ClubName", "") or ""

                data.append(
                    {
                        "id": car_idx,
                        "pos": pos,
                        "pos_gain": pos_gain,
                        "driver": name,
                        "car_number": car_num,
                        "car_logo": car_logo,
                        "license": lic_str,
                        "license_color": lic_color,
                        "class_id": class_id,
                        "class_color": class_color,
                        "irating": drv.get("IRating", 0),
                        "ir_delta": "",
                        "last_lap": last,
                        "gap": gap,
                        "incidents": inc_val,
                        "country": country,
                    }
                )

            data.sort(key=lambda d: d["pos"])
        except Exception as e:
            print("[IRacingClient] Erro standings:", e)

        return data

    # -------------------
    # Session Info
    # -------------------
    def _get_session_info(self):
        try:
            session_info = self.ir["SessionInfo"] or {}
            weekend_info = self.ir["WeekendInfo"] or {}

            sof_general = 0
            class_sof = {}
            laps_total = 0
            laps_completed = 0
            session_length_str = "--"
            remain_str = None

            if session_info and "Sessions" in session_info:
                sessions = session_info["Sessions"]
                if sessions and isinstance(sessions, list):
                    first_session = sessions[0]

                    sof_general = first_session.get("StrengthOfField", 0)
                    laps_total = first_session.get("SessionLaps", 0)
                    laps_completed = first_session.get("ResultsLapsComplete", 0)

                    results = first_session.get("ResultsPositions", [])
                    if results and isinstance(results, list):
                        for pos in results:
                            class_id = pos.get("CarClassID")
                            sof_val = pos.get("StrengthOfField")
                            if class_id and sof_val:
                                class_sof[class_id] = sof_val

                    if laps_total and laps_total > 0:
                        session_length_str = f"{laps_completed}/{laps_total} voltas"
                    else:
                        session_time_total = first_session.get("SessionTime", 0)
                        if isinstance(session_time_total, (int, float)) and session_time_total > 0:
                            h = int(session_time_total // 3600)
                            m = int((session_time_total % 3600) // 60)
                            if h > 0:
                                session_length_str = f"{h}h{m:02d}m"
                            else:
                                session_length_str = f"{m}m"

                        time_remain = self.ir["SessionTimeRemain"] or 0
                        if isinstance(time_remain, (int, float)) and time_remain > 0:
                            h = int(time_remain // 3600)
                            m = int((time_remain % 3600) // 60)
                            s = int(time_remain % 60)
                            if h > 0:
                                remain_str = f"{h}:{m:02d}:{s:02d}"
                            else:
                                remain_str = f"{m:02d}:{s:02d}"

            track_temp = 0
            if weekend_info and "TrackSurfaceTemp" in weekend_info:
                raw_temp = weekend_info["TrackSurfaceTemp"]
                if isinstance(raw_temp, str):
                    try:
                        track_temp = float(raw_temp.split()[0])
                    except Exception:
                        track_temp = 0
                elif isinstance(raw_temp, (int, float)):
                    track_temp = raw_temp

            my_id = self.ir["PlayerCarIdx"]

            return {
                "sof": sof_general,
                "class_sof": class_sof,
                "session_length": session_length_str,
                "time_remain": remain_str,
                "track_temp": f"{track_temp:.1f} °C" if isinstance(track_temp, (int, float)) else "--",
                "my_driver_id": my_id,
            }
        except Exception as e:
            print("[IRacingClient] Erro sessão:", e)
            return {}

    # -------------------
    # Fuel Info
    # -------------------
    def _get_fuel(self):
        try:
            level = self.ir["FuelLevel"]
            cap = self.ir["FuelCapacity"]
            use_per_lap = self.ir["FuelUsePerLap"]
            laps_rem = 0

            if (
                isinstance(level, (int, float))
                and isinstance(use_per_lap, (int, float))
                and use_per_lap > 0
            ):
                laps_rem = int(level / use_per_lap)

            return {
                "level": float(level) if isinstance(level, (int, float)) else 0,
                "capacity": float(cap) if isinstance(cap, (int, float)) else 0,
                "use_per_lap": float(use_per_lap) if isinstance(use_per_lap, (int, float)) else 0,
                "laps": laps_rem,
            }
        except Exception as e:
            print("[IRacingClient] Erro fuel:", e)
            return {}

    # -------------------
    # Car Left/Right
    # -------------------
    def _get_car_lr(self):
        try:
            val = self.ir["CarLeftRight"]

            status_map = {
                0: "none",
                1: "clear",
                2: "left",
                3: "right",
                4: "both",
            }

            status = status_map.get(val, "none")
            return {"val": val, "status": status}
        except Exception as e:
            print(f"[ERROR CarLR] {e}")
            return {"val": 0, "status": "none"}
