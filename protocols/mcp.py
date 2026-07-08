"""
mcp.py — Protocolo MCP (Model Context Protocol) para transferencias de agentes.

Define:
- Esquema de payload JSON para estado compartido
- Validación de transferencias entre agentes
- Resolución de conflictos de estado
- Detección de palabras clave para escalamiento
"""

import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

try:
    from core.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# Definición del protocolo MCP
MCP_SCHEMA: Dict[str, Any] = {
    "campos_requeridos": [
        "protocolo_mcp", "version", "timestamp", "datos_sesion", "resolucion_conflictos"
    ],
    "version_soportada": "1.0"
}

# Palabras clave que indican escalamiento técnico
PALABRAS_CLAVE_TECNICAS: List[str] = [
    "cuello de botella", "bottleneck", "watts", "voltaje", "fuente de poder",
    "compatibilidad", "transferir", "especialista", "soporte técnico",
    "no puedo responder", "no estoy capacitado", "derivar", "escalar",
    "técnico", "hardware avanzado", "overclock", "tdp", "pcie",
    "chipset", "bios", "firmware", "latencia", "ancho de banda"
]

# Palabras clave que indican necesidad de consulta de inventario
PALABRAS_CLAVE_INVENTARIO: List[str] = [
    "tienen stock", "hay stock", "disponible", "disponibilidad", "garantía", "garantia",
    "marca", "marcas", "tienda", "almacén", "almacen", "entrega", "despacho",
    "envían", "enviaron", "recojo", "en stock", "precio", "oferta", "descuento"
]


def validar_payload_mcp(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Valida que el payload MCP cumpla con el esquema definido.
    
    Args:
        payload: Diccionario con estructura MCP.
    
    Returns:
        Tupla (es_válido, mensaje_error). Si es válido, mensaje_error es None.
    """
    if not isinstance(payload, dict):
        return False, "payload no es un diccionario"
    
    for campo in MCP_SCHEMA["campos_requeridos"]:
        if campo not in payload:
            return False, f"Campo requerido ausente: {campo}"
    
    version = payload.get("version")
    if version != MCP_SCHEMA["version_soportada"]:
        return False, f"Versión no soportada: {version} (esperado: {MCP_SCHEMA['version_soportada']})"
    
    return True, None


def generar_payload_mcp(agente_origen: str, agente_destino: str, motivo: str,
                        shared_memory_data: Dict[str, Any],
                        historial_resumen: str = "") -> Dict[str, Any]:
    """Genera el estado compartido MCP como payload JSON para la transferencia entre agentes.
    
    Args:
        agente_origen: Nombre del agente que transfiere.
        agente_destino: Nombre del agente que recibe.
        motivo: Razón de la transferencia.
        shared_memory_data: Datos de memoria compartida.
        historial_resumen: Resumen del historial de conversación.
    
    Returns:
        Diccionario con estructura MCP completa.
    
    Raises:
        ValueError: Si parámetros requeridos son inválidos.
    """
    if not agente_origen or not agente_destino or not motivo:
        raise ValueError("Parámetros de agentes y motivo son requeridos")
    
    estado_compartido_mcp = {
        "protocolo_mcp": "Activo",
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "datos_sesion": {
            "cliente_perfil": shared_memory_data.get("cliente_perfil", {}),
            "consulta_stock": shared_memory_data.get("consulta_stock", {}),
            "estado_conversacion": motivo,
            "historial_preservado": historial_resumen
        },
        "resolucion_conflictos": {
            "estrategia": "Priorizar_estabilidad_hardware",
            "fallback": "Consultar_catalogo_compatible",
            "timeout_segundos": 30,
            "conflictos_detectados": []
        },
        "metricas_transferencia": {
            "agente_origen": agente_origen,
            "agente_destino": agente_destino,
            "motivo_escalamiento": motivo
        }
    }
    
    logger.info(
        f"Payload MCP generado: {agente_origen} → {agente_destino} "
        f"({motivo[:50]}...)"
    )
    return estado_compartido_mcp


def resolver_conflictos_mcp(payload: Dict[str, Any], verbose: bool = True) -> Dict[str, Any]:
    """Algoritmo de resolución de conflictos de estado en payload de transferencia.
    
    Verifica:
    - Consistencia entre garantía informada y producto de interés
    - Consistencia entre entrega coordinada y stock confirmado
    
    Args:
        payload: Payload MCP a validar y resolver.
        verbose: Si True, registra conflictos encontrados.
    
    Returns:
        Payload actualizado con conflictos resueltos.
    """
    datos_sesion = payload.get("datos_sesion", {})
    consulta_stock = datos_sesion.get("consulta_stock", {})
    conflictos: List[str] = []

    # Regla de Consistencia 1: Garantía informada requiere producto de interés
    if consulta_stock.get("garantia_informada") and not consulta_stock.get("producto_interes"):
        conflictos.append("Garantía informada sin producto definido → CORREGIDO")
        consulta_stock["garantia_informada"] = False

    # Regla de Consistencia 2: Entrega coordinada requiere stock confirmado
    if consulta_stock.get("entrega_coordinada") and not consulta_stock.get("stock_confirmado"):
        conflictos.append("Entrega coordinada sin stock confirmado → CORREGIDO")
        consulta_stock["entrega_coordinada"] = False

    # Regla de Consistencia 3: Autodetectar productos comunes
    if not consulta_stock.get("producto_interes"):
        texto_datos = json.dumps(datos_sesion).lower()
        for producto in ["rtx 4060", "rtx 4070", "rtx 4080", "i7", "ryzen 7"]:
            if producto in texto_datos:
                conflictos.append(f"Producto autodetectado: {producto.upper()}")
                consulta_stock["producto_interes"] = producto.upper()
                break

    payload["resolucion_conflictos"]["conflictos_detectados"] = conflictos
    
    if conflictos and verbose:
        logger.info(f"Conflictos MCP resueltos: {conflictos}")
        
    return payload


def mostrar_transferencia_mcp(payload: Dict[str, Any], verbose: bool = True) -> bool:
    """Muestra el proceso de transferencia MCP con validación y resolución.
    
    Args:
        payload: Payload MCP a procesar.
        verbose: Si True, imprime detalles en consola.
    
    Returns:
        True si validación fue exitosa, False en caso contrario.
    """
    es_valido, error_msg = validar_payload_mcp(payload)

    if es_valido:
        payload = resolver_conflictos_mcp(payload, verbose)

    if verbose:
        print("\n" + "=" * 65)
        print("  [Sistema MCP]: Iniciando transferencia jerárquica...")
        print("  [Sistema MCP]: Validando payload contra esquema MCP...")
        estado = "VALIDADO ✓" if es_valido else f"ERROR: {error_msg}"
        print(f"  [Sistema MCP]: Estado del payload: {estado}")
        print("  [Sistema MCP]: Payload JSON final transmitido:")
        print("=" * 65)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print("=" * 65)
        if es_valido:
            print("  [Sistema MCP]: Transferencia exitosa.")
        else:
            print(f"  [Sistema MCP]: ADVERTENCIA - Transferencia con errores.")
        print("=" * 65 + "\n")
    
    logger.info(f"Transferencia MCP: {'Exitosa' if es_valido else 'Falló'}")
    return es_valido


def necesita_escalamiento(respuesta: str) -> bool:
    """Determina si la respuesta indica necesidad de escalamiento técnico.
    
    Args:
        respuesta: Texto de respuesta o consulta del usuario.
    
    Returns:
        True si se detectan palabras técnicas complejas, False en caso contrario.
    """
    if not respuesta or not isinstance(respuesta, str):
        return False
    
    respuesta_lower = respuesta.lower()
    
    # Contar coincidencias de palabras técnicas
    coincidencias = sum(1 for p in PALABRAS_CLAVE_TECNICAS if p in respuesta_lower)
    if coincidencias >= 2:
        logger.debug(f"Escalamiento técnico detectado ({coincidencias} palabras clave)")
        return True
    
    # Frases explícitas de delegación
    frases_delegacion = [
        "transferir al especialista", "derivar al especialista", "soporte técnico",
        "no estoy capacitado", "te paso con el especialista", "especialista técnico"
    ]
    for frase in frases_delegacion:
        if frase in respuesta_lower:
            logger.debug(f"Frase de delegación detectada: '{frase}'")
            return True
    
    return False


def necesita_inventario(respuesta: str) -> bool:
    """Determina si la respuesta indica necesidad de consulta de inventario.
    
    Args:
        respuesta: Texto de respuesta o consulta del usuario.
    
    Returns:
        True si se detectan palabras de inventario, False en caso contrario.
    """
    if not respuesta or not isinstance(respuesta, str):
        return False
    
    respuesta_lower = respuesta.lower()
    
    # Contar coincidencias de palabras de inventario
    coincidencias = sum(1 for p in PALABRAS_CLAVE_INVENTARIO if p in respuesta_lower)
    if coincidencias >= 2:
        logger.debug(f"Consulta de inventario detectada ({coincidencias} palabras clave)")
        return True
    
    # Frases explícitas
    frases_inventario = [
        "pasar al inventario", "agente de inventario", "validar stock",
        "consultar stock", "recojo en tienda", "marcas disponibles",
        "política de garantía"
    ]
    for frase in frases_inventario:
        if frase in respuesta_lower:
            logger.debug(f"Frase de inventario detectada: '{frase}'")
            return True
    
    return False
