"""
metrics.py — Rastreador de métricas de rendimiento del Swarm.

Registra latencias, tokens consumidos, y resultados de pruebas
para evaluación de la arquitectura multiagente.
"""

import time
from typing import List, Dict, Any, Optional
from statistics import mean, median, stdev


class MetricsTracker:
    """Registra métricas de rendimiento y resultados de pruebas.
    
    Métricas principales:
    - Tokens consumidos totales por llamadas a LLM
    - Latencias por llamada al modelo
    - Tasa de éxito en test cases
    - Tiempo total de ejecución
    """
    
    def __init__(self) -> None:
        """Inicializa el rastreador de métricas."""
        self.global_tokens: int = 0
        self.total_llamadas: int = 0
        self.latencias: List[float] = []
        self.resultados_pruebas: List[Dict[str, Any]] = []
        self.start_time: float = time.time()

    def registrar_llamada(self, tokens: Optional[int], latencia: float) -> None:
        """Registra una llamada exitosa al modelo.
        
        Args:
            tokens: Número de tokens consumidos (None si no disponible).
            latencia: Tiempo de ejecución en segundos.
        
        Raises:
            ValueError: Si latencia es negativa.
        """
        if latencia < 0:
            raise ValueError(f"Latencia no puede ser negativa: {latencia}")
        
        self.total_llamadas += 1
        if tokens is not None and tokens > 0:
            self.global_tokens += tokens
        self.latencias.append(float(latencia))

    def registrar_resultado(self, caso: str, exito: bool, agente: str, **kwargs) -> None:
        """Registra el resultado de un caso de prueba.
        
        Args:
            caso: Identificador del caso (ej. 'C-01').
            exito: True si el caso pasó, False si falló.
            agente: Nombre del agente que procesó el caso.
            **kwargs: Datos adicionales a registrar.
        """
        if not isinstance(caso, str) or not caso.strip():
            raise ValueError(f"caso inválido: {caso}")
        if not isinstance(agente, str) or not agente.strip():
            raise ValueError(f"agente inválido: {agente}")
        
        resultado = {
            "caso": caso,
            "exito": bool(exito),
            "agente": agente,
            "timestamp": time.time()
        }
        resultado.update(kwargs)
        self.resultados_pruebas.append(resultado)

    def obtener_estadisticas_latencia(self) -> Dict[str, float]:
        """Calcula estadísticas de latencia.
        
        Returns:
            Diccionario con promedio, mín, máx, mediana y desv. estándar.
        """
        if not self.latencias:
            return {
                "promedio": 0.0,
                "minima": 0.0,
                "maxima": 0.0,
                "mediana": 0.0,
                "desv_estandar": 0.0
            }
        
        return {
            "promedio": round(mean(self.latencias), 3),
            "minima": round(min(self.latencias), 3),
            "maxima": round(max(self.latencias), 3),
            "mediana": round(median(self.latencias), 3),
            "desv_estandar": round(stdev(self.latencias), 3) if len(self.latencias) > 1 else 0.0
        }

    def obtener_tasa_exito(self) -> float:
        """Calcula la tasa de éxito en pruebas.
        
        Returns:
            Porcentaje de pruebas exitosas (0-100).
        """
        if not self.resultados_pruebas:
            return 0.0
        exitosas = sum(1 for r in self.resultados_pruebas if r["exito"])
        return round((exitosas / len(self.resultados_pruebas)) * 100, 2)

    def imprimir_reporte(self, modelo: str) -> None:
        """Imprime un reporte detallado de métricas del sistema.
        
        Args:
            modelo: Nombre del modelo usado (ej. 'gemini-2.5-flash').
        """
        end_time = time.time()
        tiempo_total = end_time - self.start_time
        stats_latencia = self.obtener_estadisticas_latencia()
        tasa_exito = self.obtener_tasa_exito()

        print("\n" + "=" * 65)
        print("            REPORTE DE METRICAS DEL SISTEMA")
        print("=" * 65)
        print(f"  Tiempo total de ejecución    : {tiempo_total:.2f} segundos")
        print(f"  Tokens totales consumidos    : {self.global_tokens} tokens")
        print(f"  Llamadas totales al modelo   : {self.total_llamadas}")
        print("-" * 65)
        print(f"  Latencia promedio            : {stats_latencia['promedio']:.3f}s")
        print(f"  Latencia mínima              : {stats_latencia['minima']:.3f}s")
        print(f"  Latencia máxima              : {stats_latencia['maxima']:.3f}s")
        print(f"  Mediana                      : {stats_latencia['mediana']:.3f}s")
        if len(self.latencias) > 1:
            print(f"  Desv. Estándar               : {stats_latencia['desv_estandar']:.3f}s")
        print("-" * 65)
        if self.resultados_pruebas:
            exitosas = sum(1 for r in self.resultados_pruebas if r["exito"])
            print(f"  Tasa de éxito                : {tasa_exito}% ({exitosas}/{len(self.resultados_pruebas)} pruebas)")
        print(f"  Topología de Arquitectura    : Delegación Jerárquica (Swarm)")
        print(f"  Protocolo de Estado          : MCP (Model Context Protocol)")
        print(f"  Modelo utilizado             : {modelo}")
        
        if self.resultados_pruebas:
            print("-" * 65)
            print("  RESULTADOS POR CASO DE PRUEBA:")
            print("-" * 65)
            for r in self.resultados_pruebas:
                estado = "✓ PASS" if r["exito"] else "✗ FAIL"
                print(f"    [{estado}] {r['caso']:5s} | Agente: {r['agente']}")
        
        print("=" * 65 + "\n")
