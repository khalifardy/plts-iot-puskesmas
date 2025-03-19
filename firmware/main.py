from machine import Pin
from network_manager import NetworkManager
import time

# Membuat koneksi MQTT global 
global MESSAGE_INTERVAL

MESSAGE_INTERVAL = 5

def main():
    print("Starting sensor monitoring system . . .")
    
    # Inisialisasi variabel global
    nm = NetworkManager()
    nm.auto_connect()
    
    from sensor import Temperature, PZEM_RS485

    
    #inisialisaasi sensor
    temp_sensor = Temperature(1)
    pzem1 = PZEM_RS485(id_sensor=2)
    pzem2 = PZEM_RS485(slave_addr=0x02,id_sensor=3)
    
    last_temp_time = 0
    last_pzem1_time = 0
    last_pzem2_time = 0
    
    print("Monitoring loop started . . .")
    
    while True:
        current_time = time.time()
        
        #Baca dan kirim data sensor suhu
        
        if (current_time - last_temp_time) >= MESSAGE_INTERVAL:
            temp = temp_sensor.send_temperature_once()
            if temp is not None:
                print(f"Temperature:{temp}°C")
            last_temp_time = current_time
        
        #Baca dan kirim data sensor PZEM1
        if (current_time - last_pzem1_time) >= MESSAGE_INTERVAL:
            pzem1_data_tegangan = pzem1.send_data_once("voltage")
            if pzem1_data_tegangan is not None:
                print(f"PZEM1: Voltage:{pzem1_data_tegangan}V")
            
            pzem1_data_arus = pzem1.send_data_once("current")
            if pzem1_data_arus is not None:
                print(f"PZEM1: Current:{pzem1_data_arus}A")
        
            pzem1_data_daya = pzem1.send_data_once("power")
            if pzem1_data_daya is not None:
                print(f"PZEM1: Power:{pzem1_data_daya}W")

            pzem1_data_energi = pzem1.send_data_once("energy")
            if pzem1_data_energi is not None:
                print(f"PZEM1: Energy:{pzem1_data_energi}Wh")
            last_pzem1_time = current_time
        
        #Baca dan kirim data sensor PZEM2
        if (current_time - last_pzem2_time) >= MESSAGE_INTERVAL:
            pzem2_data_tegangan = pzem2.send_data_once("voltage")
            if pzem2_data_tegangan is not None:
                print(f"PZEM2: Voltage:{pzem2_data_tegangan}V")

            pzem2_data_arus = pzem2.send_data_once("current")
            if pzem2_data_arus is not None:
                print(f"PZEM2: Current:{pzem2_data_arus}A")

            pzem2_data_daya = pzem2.send_data_once("power")
            if pzem2_data_daya is not None:
                print(f"PZEM2: Power:{pzem2_data_daya}W")
  
            pzem2_data_energi = pzem2.send_data_once("energy")
            if pzem2_data_energi is not None:
                print(f"PZEM2: Energy:{pzem2_data_energi}Wh")
            last_pzem2_time = current_time
        
        time.sleep(10)
    
    

if __name__ == "__main__":
    #berikan waktu untuk sistem dimulai dan koneksi Wifi/MQQT
    
    time.sleep(3)
    print("System initializing... ")
    
    try:
        main()
    except Exception as e:
        print("An error occured:", e)
        
        for i in range (10,0,-1):
            print(f"Restarting in {i} seconds...")
            time.sleep(1)
        
        #restart program
        import machine
        machine.reset()
        
        