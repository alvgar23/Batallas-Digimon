# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 13:24:13 2020


ATENCIÓN: RIVALES QUE ME SALEN EMPATE EN DUELOS IMPARES:
    ARM-AGU-TEN
    NUM-IMP-WOR
    PAL-BET-BIY
    GOM-BET-PAL
    IMP-SUK-CAND

@author: alvar
"""
#Compara cartas de digimon que le pasamos como archivo de texto
# un digimon tiene esta estructura:
# ["abrev.", "nombre", defensa, ataque1, ataque2, fuerza, velocidad, media]
# Criterio1 para victoria: puntos por def+atq1+atq2+fuerza+velocidad
# Criterio2: Si empatan, la media da un punto extra
# Criterio3: Si empatan, la mayor diferencia entre atq2 y defensa rival

# Esto se inicializa fuera del while para que quede registrado el palmarés
palmares = []

#Queremos que se repita el torneo unas 5 veces
repeticiones = 0
while repeticiones < 2:

    # Primero vamos a ver cuántos Digimon hay en el documento
    # Cada Digimon en principio tendrá 8 elementos en la lista
    archivo = open("datos_digimon_pruebas.txt", "r") 
    num_lineas = 0
    while True:
        linea = archivo.readline().strip()
        if linea == "":
            break
        else:
            num_lineas += 1
    print()
    print("El documento tiene", num_lineas, "líneas.")
    print("El documento tiene", int(num_lineas/8), "Digimon.")
    archivo.close()
    
    
    #Volvemos a abrir para almacenar los Digimon en un único bombo. Es una lista 
    #que engloba a los participantes, cuyos datos se incluyen en listas también
    archivo = open("datos_digimon_pruebas.txt", "r") 
    participantes = []    #Contendrá a los Digimon  [[AGU],[GAB],..]
    participante = []    #contendrá a cada Digimon antes de pasarlo a partes
    
    #Para saber cuántos datos hay en cada digimon
    num_datos_digimon = 8
    aux = num_datos_digimon #para no perder el valor original 
    contador = 0
    
    while True:
        linea = archivo.readline().strip() #Lee la línea y borra salto de línea
        if linea == "":
            break  #Salimos del bucle cuando se acaban los equipos (linea vacia)
        else:
            if contador < num_datos_digimon:   #Cada digimon tiene 8 elementos
                participante.append(linea)
                contador += 1
            if contador == num_datos_digimon and contador <= num_lineas:
                num_datos_digimon += aux
                participantes.append(participante) 
                participante = []  #es un bombo provisional, valor se guardó en participantes
    #Le devolvemos su valor original
    num_datos_digimon = aux
    
    archivo.close()
    
    num_digimon = int(num_lineas/8) #Fuera del while porque va cambiando
    # Mientras participantes sea mayor que 1 repetimos (hasta llegar a la final)
    while len(participantes) > 1:
        #Ordenamos participantes alfabéticamente
        participantes.sort()
        # Imprimimos todos los participantes, pero solo los nombres, situados en
        # la posición 1 de participantes[i]
        print()
        print("Digimon de esta ronda: ")
        for i in range(len(participantes)):
            if i in range(0,9):
                print(i+1, " -",participantes[i][1])
            else:
                print(i+1, "-",participantes[i][1])
        print()
        
        # Creamos lista con número de batallas
        batallas = []
        
        #Si son impares no pasa nada, habrá triple batalla en batallas[0] 
        for i in range(int(num_digimon/2)): #convertimos a int porque era float
            batallas.append([])   
         
        from random import choice
        
        #Ahora hacemos el sorteo de las batallas
        contador = 0
        while len(participantes) != 0:
            carta = choice(participantes)
            batallas[contador].append(carta)
            participantes.remove(carta)
            contador += 1   
            if contador == int(num_digimon/2):
                contador = 0
        
        #Intentamos imprimirlo de forma bonita
        # queremos solo mostrar los nombres de los digimon (no los datos)
        muestra = []
        for i in range(len(batallas)):
            muestra.append([])      #creamos lista vacía de muestra
            
        for i in range(len(batallas)):
            for j in range(len(batallas[i])):
                muestra[i].append(batallas[i][j][1]) #rellenamos muestra con batallas
            print(muestra[i])
        
        # Empezamos las batallas!
        
        #Primero creamos una lista para los puntajes. Debe ser igual a muestra
        puntos = []
        for i in range(len(batallas)):
            puntos.append([])      #creamos lista vacía de muestra
        
        # Y la rellenamos con los puntos iniciales (0)
        for i in range(len(batallas)):
            for j in range(len(batallas[i])):
                puntos[i].append(0) #rellenamos con ceros
            
        puntos1 = 0
        puntos2 = 0
        puntos3 = 0
        # Ahora comparamos para digimon pares
        if num_digimon %2 == 0:
            for i in range(len(batallas)):
                for j in range(0,len(batallas[i]),2): #Salta de dos en dos para comparar
                    for k in range(2,len(batallas[i][j])-1):
                        if batallas[i][j][k] > batallas[i][j+1][k]:
                            puntos1 += 1
                        if batallas[i][j][k] < batallas[i][j+1][k]:
                            puntos2 += 1
                        puntos[i][j] = puntos1
                        puntos[i][j+1] = puntos2     
                    puntos1 = 0
                    puntos2 = 0
                    
        #Ahora para digimon impares
        #Ponemos puntuación doble para asegurar ganador justo si hay empates
        if num_digimon %2 != 0:
            for i in range(len(batallas)):
                if i == 0: #Salta 3 para comparar porque hay 3 digimon
                    for j in range(0,len(batallas[i]),3): 
                        for k in range(2,len(batallas[i][j])-1):
                            # 1 vs 2
                            if batallas[i][j][k] > batallas[i][j+1][k]:
                                puntos1 += 2
                            if batallas[i][j][k] < batallas[i][j+1][k]:
                                puntos2 += 2
                            # 1 vs 3
                            if batallas[i][j][k] > batallas[i][j+2][k]:
                                puntos1 += 2
                            if batallas[i][j][k] < batallas[i][j+2][k]:
                                puntos3 += 2
                            # 2 vs 3
                            if batallas[i][j+1][k] > batallas[i][j+2][k]:
                                puntos2 += 2
                            if batallas[i][j+1][k] < batallas[i][j+2][k]:
                                puntos3 += 2    
                            puntos[i][j] = puntos1
                            puntos[i][j+1] = puntos2
                            puntos[i][j+2] = puntos3
                        puntos1 = 0
                        puntos2 = 0
                        puntos3 = 0
                if i != 0: # saltará solo 2 como normalmente
                    for j in range(0,len(batallas[i]),3): 
                        for k in range(2,len(batallas[i][j])-1):
                            # 1 vs 2
                            if batallas[i][j][k] > batallas[i][j+1][k]:
                                puntos1 += 1
                            if batallas[i][j][k] < batallas[i][j+1][k]:
                                puntos2 += 1
                            puntos[i][j] = puntos1
                            puntos[i][j+1] = puntos2
                        puntos1 = 0
                        puntos2 = 0
        
        #Imprimimos de forma bonita
        print()
        print("Resultados:")
        for i in range(len(batallas)):
                print(muestra[i], puntos[i])
        
        # si hay empate tenemos en cuenta la media (batallas[i][j][7])
        #desempate1 para digimon pares
        if num_digimon %2 == 0:
            for i in range(len(puntos)):
                for j in range(0,len(puntos[i]),2):
                    # si los 2 tienen los mismos puntos
                    if puntos[i][j] == puntos[i][j+1]:
                        if batallas[i][j][7] > batallas[i][j+1][7]:
                            puntos[i][j] += 1
                        if batallas[i][j][7] < batallas[i][j+1][7]:
                            puntos[i][j+1] += 1  
        
        # desempate1 para digimon impares
        # puntuamos doble por si hay empate, asi ganador justo
        if num_digimon %2 != 0:
            for i in range(len(puntos)):
                if i == 0: 
                    for j in range(0,len(puntos[i]),3):
                        #empate 1 vs 2
                        if puntos[i][j] == puntos[i][j+1]:
                            if batallas[i][j][7] > batallas[i][j+1][7]:
                                puntos[i][j] += 2
                            if batallas[i][j][7] < batallas[i][j+1][7]:
                                puntos[i][j+1] += 2  
                        #empate 1 vs 3
                        elif puntos[i][j] == puntos[i][j+2]:
                            if batallas[i][j][7] > batallas[i][j+2][7]:
                                puntos[i][j] += 2
                            if batallas[i][j][7] < batallas[i][j+2][7]:
                                puntos[i][j+2] += 2 
                        #empate 2 vs 3
                        elif puntos[i][j+1] == puntos[i][j+2]:
                            if batallas[i][j+1][7] > batallas[i][j+2][7]:
                                puntos[i][j+1] += 2
                            if batallas[i][j+1][7] < batallas[i][j+2][7]:
                                puntos[i][j+2] += 2 
                if i != 0:
                    for j in range(0,len(puntos[i]),2):
                        # si los 2 tienen los mismos puntos
                        if puntos[i][j] == puntos[i][j+1]:
                            if batallas[i][j][7] > batallas[i][j+1][7]:
                                puntos[i][j] += 2
                            if batallas[i][j][7] < batallas[i][j+1][7]:
                                puntos[i][j+1] += 2  
        
        #Imprimimos de forma bonita
        print()
        print("Desempate 1:")
        for i in range(len(batallas)):
                print(muestra[i], puntos[i])
        
        #Si después de incluir la media sigue habiendo empate debemos incluir nuevos 
        #parámetros de desempate. Como la diferencia entre ataque2 y defensa rival
        #desempate2 para digimon pares
        if num_digimon %2 == 0:
            for i in range(len(puntos)):
                for j in range(0,len(puntos[i]),2):
                    if puntos[i][j] == puntos[i][j+1]:
            #pongo paréntesis para dividir código en 2 líneas (too long)
                        if (int(batallas[i][j][4]) - int(batallas[i][j+1][2]) 
                            > int(batallas[i][j+1][4]) - int(batallas[i][j][2])):
                            puntos[i][j] += 1
                        if (int(batallas[i][j][4]) - int(batallas[i][j+1][2])  
                        < int(batallas[i][j+1][4]) - int(batallas[i][j][2])):
                            puntos[i][j+1] += 1  
        
        #desempate2 para digimons impares, solo si los 3 son iguales
        if num_digimon %2 != 0:
            for i in range(len(puntos)):
                if i == 0:
                   for j in range(0,len(puntos[i]),3):
                       #empate entre 1 y 2
                       if puntos[i][j] == puntos[i][j+1]:
                           if (int(batallas[i][j][4]) - int(batallas[i][j+1][2])
                               > int(batallas[i][j+1][4]) - int(batallas[i][j][2])):
                               puntos[i][j] += 1
                           if (int(batallas[i][j][4]) - int(batallas[i][j+1][2])
                               < int(batallas[i][j+1][4]) - int(batallas[i][j][2])):
                               puntos[i][j+1] += 1
                       #empate entre 1 y 3
                       if puntos[i][j] == puntos[i][j+2]:
                           if (int(batallas[i][j][4]) - int(batallas[i][j+2][2])
                               > int(batallas[i][j+2][4]) - int(batallas[i][j][2])):
                               puntos[i][j] += 1
                           if (int(batallas[i][j][4]) - int(batallas[i][j+2][2])
                               < int(batallas[i][j+2][4]) - int(batallas[i][j][2])):
                               puntos[i][j+2] += 1
                       #empate entre 2 y 3
                       if puntos[i][j+1] == puntos[i][j+2]:
                           if (int(batallas[i][j+1][4]) - int(batallas[i][j+2][2])
                               > int(batallas[i][j+2][4]) - int(batallas[i][j+1][2])):
                               puntos[i][j+1] += 1
                           if (int(batallas[i][j+1][4]) - int(batallas[i][j+2][2])
                               < int(batallas[i][j+2][4]) - int(batallas[i][j+1][2])):
                               puntos[i][j+2] += 1
                if i != 0:
                    for j in range(0,len(puntos[i]),2):
                        if puntos[i][j] == puntos[i][j+1]:
                            if (int(batallas[i][j][4]) - int(batallas[i][j+1][2])
                               > int(batallas[i][j+1][4]) - int(batallas[i][j][2])):
                                puntos[i][j] += 1
                            if (int(batallas[i][j][4]) - int(batallas[i][j+1][2])
                               < int(batallas[i][j+1][4]) - int(batallas[i][j][2])):
                                puntos[i][j+1] += 1
        
        #Imprimimos de forma bonita
        print()
        print("Desempate 2:")
        for i in range(len(batallas)):
                print(muestra[i], puntos[i])
        
        # Ahora guardamos en participantes a los ganadores
        # para que vuelva a empezar
        # primero si son pares
        if num_digimon %2 == 0:
            for i in range(len(puntos)):
                for j in range(0,len(puntos[i]),2):
                    if puntos[i][j] > puntos[i][j+1]:
                        participantes.append(batallas[i][j])
                    if puntos[i][j] < puntos[i][j+1]:
                        participantes.append(batallas[i][j+1])
                    #Si empatan y son pares desempate 4:
                    if puntos[i][j] == puntos[i][j+1]:
                        if (int(batallas[i][j][3]) - int(batallas[i][j+1][2])
                               > int(batallas[i][j+1][3]) - int(batallas[i][j][2])):
                            participantes.append(batallas[i][j])
                        if (int(batallas[i][j][3]) - int(batallas[i][j+1][2])
                               < int(batallas[i][j+1][3]) - int(batallas[i][j][2])):
                            participantes.append(batallas[i][j+1])
                        
        
        # ahora para impares
        if num_digimon %2 != 0:
            for i in range(len(puntos)):
                if i == 0:
                    for j in range(0,len(puntos[i]),3):
                        # Si 1 gana a 2 y a 3
                        if puntos[i][j] > puntos[i][j+1] and puntos[i][j] > puntos[i][j+2]:
                            participantes.append(batallas[i][j])
                        # Si 2 gana a 1 y a 3
                        if puntos[i][j+1] > puntos[i][j] and puntos[i][j+1] > puntos[i][j+2]:
                            participantes.append(batallas[i][j+1])
                        # Si 3 gana a 1 y a 2
                        if puntos[i][j+2] > puntos[i][j] and puntos[i][j+2] > puntos[i][j+1]:
                            participantes.append(batallas[i][j+2]) 
                if i != 0:
                    for j in range(0,len(puntos[i]),2):
                        if puntos[i][j] > puntos[i][j+1]:
                            participantes.append(batallas[i][j])
                        if puntos[i][j] < puntos[i][j+1]:
                            participantes.append(batallas[i][j+1])
                        #Si empatan y son impares desempate4:
                        if puntos[i][j] == puntos[i][j+1]:
                            if (int(batallas[i][j][3]) - int(batallas[i][j+1][2])
                               > int(batallas[i][j+1][3]) - int(batallas[i][j][2])):
                                participantes.append(batallas[i][j])
                            if (int(batallas[i][j][3]) - int(batallas[i][j+1][2])
                               < int(batallas[i][j+1][3]) - int(batallas[i][j][2])):
                                participantes.append(batallas[i][j+1])
                      
        
        # E informamos que los digimon serán la mitad
        num_digimon = int(num_digimon/2)
        
        #queremos parar un poco el tiempo para ver bien el programa
        from time import sleep
        
        #Queremos crear un contador de victorias para el ganador
        # Cuando solo quede 1 participante es el ganador
        # Estamos creando una lista palmarés que va sumando las victorias e 
        #incluyendo a los ganadores
        if len(participantes) == 1:
            for i in range(len(muestra)):
                for j in range(len(muestra[i])):
                    if muestra[i][j] in participantes[i]:
                        if muestra[i][j] not in palmares:
                            victorias = 1
                            palmares.append(muestra[i][j])
                            palmares.append(victorias)
                            print()
                            print(palmares)
                            sleep(0) #dormimos 2
                        elif muestra[i][j] in palmares:
                            indice = palmares.index(muestra[i][j])
                            palmares[indice+1] += 1
                            print()
                            print(palmares)
                            sleep(0) #dormimos 1.8
        sleep(0) #dormimos 5
        
        
    repeticiones += 1 #cuando hay un ganador se suma una repetición