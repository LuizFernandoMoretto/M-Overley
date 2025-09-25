import irsdk
import time

ir = irsdk.IRSDK()
ir.startup()

print("Inicializado:", ir.is_initialized)
print("Conectado:", ir.is_connected)

if not ir.is_connected:
    print("⚠️ Abra o iRacing, entre numa sessão e vá com o carro para a pista!")
    exit()

for i in range(10):  # tenta 10 vezes
    ir.freeze_var_buffer_latest()
    try:
        drivers = ir['DriverInfo']['Drivers']
        positions = ir['CarIdxPosition']
        gaps = ir['CarIdxF2Time']

        print(f"\n--- Iteração {i+1} ---")
        print("Total drivers:", len(drivers))
        for idx, drv in enumerate(drivers[:10]):  # só top 10 pra não poluir
            print(f"Idx {idx} | Nome: {drv.get('UserName')} | Pos: {positions[idx]} | Gap: {gaps[idx]}")

    except Exception as e:
        print("Erro lendo dados:", e)

    time.sleep(1)
