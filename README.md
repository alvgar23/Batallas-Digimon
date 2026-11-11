# Batallas Digimon

Simulador de combates entre Digimon escrito en Python. El proyecto empezó en 2020 con torneos automáticos a partir de estadísticas y fue creciendo hasta convertirse en un juego de cartas por turnos contra el ordenador, con distintos niveles de dificultad, selección de cartas y líneas evolutivas.

Se conservan **siete versiones históricas** del programa. No se ha modificado el código de ninguna.

## Qué se puede hacer

- **Simular torneos:** enfrentar Digimon según sus estadísticas, desempatar y elaborar clasificaciones.
- **Jugar contra el ordenador:** elegir cartas y competir contra una IA con modos Normal, Hard e Impossible.
- **Preparar una mano:** en las versiones posteriores aparece un *draft*, donde se elige una carta entre varias opciones.
- **Jugar con evoluciones:** las versiones 5 y 5.1 incorporan rutas de evolución y progresión entre niveles.

Todo funciona en la **terminal**, no hay interfaz gráfica.

## Versiones

| Archivo | Qué aporta |
| --- | --- |
| [`batallas_digimon_v1.py`](batallas_digimon_v1.py) | Versión original de 2020. Torneos a partir de un archivo TXT, comparación de cinco estadísticas y palmarés de vencedores. |
| [`batallas_digimon_v2.py`](batallas_digimon_v2.py) | Torneos desde CSV, selección de niveles, combates dobles o triples, reglas de desempate más completas y clasificación global. |
| [`batallas_digimon_v3.py`](batallas_digimon_v3.py) | Primer juego de cartas contra el ordenador: manos de tres cartas, tres turnos, tres dificultades y muerte súbita. |
| [`batallas_digimon_v4.py`](batallas_digimon_v4.py) | Introduce un draft inicial de cinco cartas, cinco turnos y una muerte súbita con nuevas elecciones. |
| [`batallas_digimon_v4.1.py`](batallas_digimon_v4.1.py) | Amplía la selección de cartas con estilos de draft, decisiones de la IA y bonificación por tipo. |
| [`batallas_digimon_v5.py`](batallas_digimon_v5.py) | Añade un torneo con progresión por niveles y rutas de evolución de Digimon. |
| [`batallas_digimon_v5.1.py`](batallas_digimon_v5.1.py) | Desarrolla un torneo de ocho batallas, con evoluciones, selección de cartas y adaptación de la personalidad de la IA. |

Más detalles en [`docs/evolucion-y-reglas.md`](docs/evolucion-y-reglas.md).

## Cómo ejecutarlo

Se necesita **Python 3**. Los scripts utilizan bibliotecas incluidas con Python, como `csv`, `random` y `collections`; no se observa un archivo de dependencias externas.

Desde la **carpeta raíz** del repositorio, por ejemplo:

```bash
python batallas_digimon_v2.py
python batallas_digimon_v4.1.py
python batallas_digimon_v5.1.py
```

También se puede ejecutar cualquiera de las demás versiones cambiando el nombre del archivo.

**Importante:** ejecuta los scripts desde la raíz. Sus rutas a los CSV, TXT y logs son relativas al directorio de trabajo. Se mantienen todos los archivos en su ubicación original para no romper esas referencias.

## Archivos de datos

| Archivo | Uso |
| --- | --- |
| `datos_digimon_todos.csv` | Base de cartas con nombre, abreviatura, estadísticas, nivel y tipo. Es la entrada principal de las versiones 2 a 5.1. |
| `linea_evolutiva.csv` | Relaciones entre Rookie, Champion, Ultimate y Mega para las versiones 5 y 5.1. |
| `datos_digimon_pruebas.txt` | Entrada usada por la versión 1. |
| `datos_digimon_pruebas.csv`, `datos_digimon_todos.txt` y otros `datos_digimon_*.txt` | Datos y pruebas conservados del desarrollo. |
| `duel_logs_v3.txt`, `duel_logs_v4.1.txt`, `duel_logs_v5.txt`, `logs.txt` | Registros históricos de combates y torneos. |
| `linea_evolutiva.txt` | Copia en formato TXT de las rutas evolutivas. |

Los archivos `datos_digimon_champion.txt` y `datos_digimon_mega.txt` están vacíos en el estado revisado del repositorio.

## Cómo se decide un duelo

Las versiones desde v2 comparan primero cinco estadísticas: defensa, ataque 1, ataque 2, fuerza y velocidad. Cuando no basta, aplican desempates adicionales, como media, diferencias entre ataques y defensa rival y ventaja de tipo. La ventaja circular de tipos sigue la relación **vaccine > virus > data > vaccine**. En versiones posteriores se introduce además una bonificación por tipo.

Las reglas exactas y su aplicación cambian entre versiones; no debe suponerse que todas producen el mismo resultado.

## Estado y límites

- Proyecto histórico: las siete versiones se conservan sin refactorizar.
- Los programas pueden pedir elecciones por teclado y generar o sobrescribir archivos de log.
- Algunas cabeceras de los scripts reutilizan descripciones de versiones anteriores; la tabla de arriba se basa también en las funciones presentes.
- No se han ejecutado pruebas completas ni se garantiza que todas las partidas o torneos terminen sin errores.
- No se han reorganizado los datos ni el código porque sus rutas relativas forman parte del funcionamiento actual.

Este repositorio documenta tanto el **simulador de torneos** como su evolución hacia un **juego de cartas Digimon contra una IA**.
