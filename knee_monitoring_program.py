#For the date to update, the RaspberryPi must be connected to wifi

from sensor_library import *
import numpy as np
import matplotlib.pyplot as plt
from gpiozero import Buzzer
from gpiozero import Button
import sys
from datetime import date, datetime
import os, time

#Create an instance of each input (sensor and buttons) and output devices (buzzer and vibration motor)
sensor = Orientation_Sensor()
vibration_object = Buzzer(26)
buzzer_object = Buzzer(22)
button1 = Button(13)
button2 = Button(19)
  
## change timezone from UST to EST
os.environ['TZ'] = 'US/Eastern'
time.tzset()
print(date.today())

#Function for inputting sensor data
def input_data():
    all_angles = sensor.euler_angles()
    angle = all_angles[0]
    if angle == None or angle >=180: 
        angle = 0 
    return angle

#rolling average
n=5
input_list = []
def rolling_average(angle):
    input_list.append(angle)
    if len(input_list)<n:
        average = None
    else:
        average = sum(input_list[-n:])/n
    return average

#Process one: Alert user with a vibration or buzzer when their knee is bent too far back
def alert_user(max_angle, safe_angle, average_angle):
    buzzer_flag = False
    if average_angle >= max_angle:
        if buzzer_object.is_active == False:
            buzzer_object.on()
            print("Buzzer turned on")
            buzzer_flag = True
        if vibration_object.is_active == True:
            vibration_object.off()
            print("Vibration motor turned off")
    elif average_angle >= safe_angle:
        if vibration_object.is_active == False: 
            vibration_object.on()
            print("Vibration motor turned on")
        if buzzer_object.is_active == True:
            buzzer_object.off()
            print("Buzzer turned off")
    elif buzzer_object.is_active == True:
        buzzer_object.off()
        print("Buzzer turned off")
    elif vibration_object.is_active == True:
        vibration_object.off()
        print("Vibration motor turned off")
    return buzzer_flag

#Store data to a text file
def store_data(data):
    output_file = open('knee_monitoring.txt','a')
    output_file.write(str(data))
    output_file.close()

#set knee_tally
knee_tally = 0
#Process 2: Graph weekly knee_tally
def compute_and_graph_knee_tally(current_date,average_angle,max_angle,day_change,buzzer_flag):
    global knee_tally
    if average_angle >= max_angle and buzzer_flag == True:
        knee_tally+=1
        print ("Knee tally is:", knee_tally)
         
    if day_change == True:
        data = str(knee_tally) +" " + str(current_date) + " "
        daily_file = open('knee_tally.txt','a')
        daily_file.write(str(data)) 
        daily_file.close()

    if button2.is_pressed == True or day_change == True:
        daily_file = open("knee_tally.txt","r") 
        a = (daily_file.read()).split()
        
        if day_change == True:
            tick_label = [a[-13],a[-11],a[-9],a[-7],a[-5],a[-3],a[-1]]
            weekly_knee_tally = [int(a[-14]),int(a[-12]),int(a[-10]),int(a[-8]),int(a[-6]),int(a[-4]),int(a[-2])]
        else:
            tick_label = [a[-11],a[-9],a[-7],a[-5],a[-3],a[-1],str(current_date)]
            weekly_knee_tally = [int(a[-12]),int(a[-10]),int(a[-8]),int(a[-6]),int(a[-4]),int(a[-2]),knee_tally]
            
        x = tick_label
        y = weekly_knee_tally
        fig = plt.figure(figsize = (10, 7))
        plt.bar(x, y, width = 0.4, color = 'green')
        plt.xlabel('Date')
        plt.ylabel('Frequency')
        plt.title('Number of Times Knee Angle Reaches/Surpasses Max Angle')
        plt.savefig('plot.png')
        daily_file.close()
        print("The graph has been updated.")
        
def main():
    global knee_tally
    day_change = False
    
    max_angle = int(input("What is the maximum knee angle recommended by your physician?: "))
    safe_angle = max_angle*0.5
    current_date = date.today()

    store_data("Angle(raw)\tAngle(avg)\tKnee Tally\n")

    while True:
        current_angle = input_data()
        average_angle = rolling_average(current_angle)
        print("Raw Angle:", current_angle,"\t Rolling Average Angle:", average_angle)

        if average_angle != None:
            buzzer_flag=alert_user(max_angle, safe_angle, average_angle)
            compute_and_graph_knee_tally(current_date,average_angle,max_angle,day_change,buzzer_flag)
    
            if current_date!=date.today():
                day_change = True
                compute_and_graph_knee_tally(current_date,average_angle,max_angle,day_change,buzzer_flag)
                current_date = date.today()
                knee_tally = 0
                day_change = False

        if average_angle != None:
            formatted_average_angle = round(average_angle,1)
        else:
            formatted_average_angle = average_angle
        
        store_data(str(round(current_angle,1))+"\t\t"+str(formatted_average_angle)+"\t\t"+str(round(knee_tally,1))+"\n")

        if button1.is_pressed == True:
            buzzer_object.off()
            vibration_object.off()
            sys.exit()
            
        time.sleep(0.2)
        
main()
