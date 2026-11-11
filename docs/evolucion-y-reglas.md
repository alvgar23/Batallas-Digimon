# Evolución del proyecto y reglas

Este documento explica qué hace cada etapa del proyecto a partir del código conservado. No es una especificación de un juego futuro ni una garantía de que todos los recorridos se hayan probado.

## 1. Torneos automáticos: v1 y v2

### v1 — 2020

`batallas_digimon_v1.py` comienza con un archivo TXT de pruebas. Cada Digimon se representa mediante ocho valores: abreviatura, nombre, defensa, ataque 1, ataque 2, fuerza, velocidad y media.

El programa enfrenta participantes en rondas eliminatorias, compara sus atributos y trata de desempatar mediante la media y el ataque frente a la defensa contraria. Repite el torneo y mantiene un palmarés de victorias.

La propia cabecera contiene anotaciones sobre empates problemáticos, por lo que conviene entender esta versión como el primer experimento, no como un motor de combate completamente resuelto.

### v2 — torneos más completos

`batallas_digimon_v2.py` pasa a usar `datos_digimon_todos.csv`, que añade nivel y tipo. Permite elegir niveles de participantes y trabajar con torneos repetidos o una clasificación global.

En cada ronda se mezclan los participantes. Si hay un número impar, se organiza un combate triple de todos contra todos; el resto se enfrenta uno contra uno. En los combates triples pueden avanzar varios participantes empatados.

La resolución de los duelos establece esta prioridad:

1. Comparar **defensa, ataque 1, ataque 2, fuerza y velocidad**, otorgando un punto por atributo superior.
2. Si hay empate, comparar la **media**.
3. Si persiste, comparar **ataque 2 menos defensa del rival**.
4. Después, **ataque 1 menos defensa del rival**.
5. Aplicar ventaja circular de tipos: **vaccine > virus > data > vaccine**.
6. Si nada decide el combate, registrar un **empate total**.

El programa puede guardar los resultados detallados en `logs.txt`.

## 2. Primer juego de cartas: v3

`batallas_digimon_v3.py` cambia el formato. Ya no se trata únicamente de observar un torneo: una persona juega contra el ordenador.

- Se elige un nivel de Digimon.
- Cada contendiente recibe una mano de **tres cartas**.
- Se juegan **tres turnos**, seleccionando una carta por turno.
- Se suman puntos por duelos ganados.
- Si el marcador final está igualado, se recurre a una **muerte súbita** con nuevas cartas.

La IA ofrece tres dificultades: **Normal**, **Hard** e **Impossible**. El código incorpora valoración de cartas y decisiones que tienen en cuenta las jugadas anteriores.

## 3. Selección inicial de cartas: v4

`batallas_digimon_v4.py` introduce el **draft**: para cada uno de los cinco huecos de la mano, el jugador elige entre tres cartas. El ordenador también recibe opciones y selecciona una.

Después se disputan **cinco turnos**. Si hay empate, la muerte súbita vuelve a presentar cartas para elegir hasta que un duelo tenga vencedor.

Se conserva el sistema de tres dificultades y se registran las decisiones en `duel_logs_v3.txt` (nombre histórico usado por esta versión).

## 4. Estilos de draft y tipos: v4.1

`batallas_digimon_v4.1.py` amplía el sistema de selección: permite elegir un **estilo de draft**, mientras que la IA puede adoptar otro. Incluye decisiones relacionadas con el tipo de carta y la memoria de sus elecciones.

También aparece una **bonificación por tipo** aplicada al combate. Los registros de esta versión se escriben en `duel_logs_v4.1.txt`.

## 5. Evoluciones y torneo: v5

`batallas_digimon_v5.py` incorpora `linea_evolutiva.csv` para relacionar cartas entre niveles: **Rookie → Champion → Ultimate → Mega**.

Combina partidas de cartas, draft, dificultades de IA y un torneo que recorre etapas evolutivas. Guarda registros en `duel_logs_v5.txt`.

## 6. Torneo ampliado e IA adaptable: v5.1

`batallas_digimon_v5.1.py` conserva la base de duelos y las rutas evolutivas. Su motor principal plantea **ocho batallas**, con rondas de cinco duelos, selección de cartas y evolución entre niveles.

Incluye funciones para detectar el estilo de juego del usuario y modificar el comportamiento o personalidad de la IA entre rondas.

A diferencia de las versiones anteriores, el archivo termina con una llamada directa a `run_game_v5_1()`, por lo que **ejecuta el juego al iniciarse o importarse**. No debe importarse esperando que solo defina funciones.

## Datos y conservación

Los CSV y TXT originales siguen en la raíz porque los programas abren archivos como `datos_digimon_todos.csv` o `linea_evolutiva.csv` por su nombre, sin construir rutas desde la ubicación del script. Mover archivos a carpetas sin modificar código podría impedir su ejecución.

Los logs ya existentes también se conservan como registro histórico. Ejecutar determinadas versiones puede **sobrescribir** el log correspondiente.

## Qué no se ha hecho

No se han corregido reglas, unificado versiones, alterado estadísticas, normalizado los nombres de los Digimon ni probado todos los recorridos. Esta documentación describe la evolución observada en los archivos originales.
