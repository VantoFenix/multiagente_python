"""
memory.py — Memoria compartida (SharedMemory) para el Swarm multiagente.

Almacena el estado conversacional, perfil del cliente y datos de transacciones
en formato JSON estructurado con validación de integridad.
"""

import json
import time
from typing import Dict, List, Any, Optional


class SharedMemory:
    """Almacén centralizado de estado de sesión del Swarm multiagente.
    
    Proporciona:
    - Perfil del cliente (nombre, presupuesto, preferencias)
    - Datos de consulta de stock (producto, marca, stock, garantía, entrega)
    - Metadatos del sistema (agente activo, timestamp, historial)
    """
    
    def __init__(self) -> None:
        """Inicializa la memoria compartida con estructura de estado por defecto."""
        self.data: Dict[str, Any] = {
            "cliente_perfil": {
                "nombre": "Invitado",
                "presupuesto": None,
                "preferencias": []
            },
            "consulta_stock": {
                "producto_interes": None,
                "marca_preferida": None,
                "stock_confirmado": False,
                "garantia_informada": False,
                "entrega_coordinada": False
            },
            "sistema": {
                "agente_activo": "agente_ventas",
                "historial_resumen": "",
                "timestamp_inicio": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
        }

    def set_active_agent(self, agent_name: str) -> None:
        """Actualiza el agente activo actual.
        
        Args:
            agent_name: Nombre del agente que toma el control.
        """
        if not agent_name or not isinstance(agent_name, str):
            raise ValueError(f"agent_name inválido: {agent_name}")
        self.data["sistema"]["agente_activo"] = agent_name.lower()

    def get_active_agent(self) -> str:
        """Obtiene el agente activo actual.
        
        Returns:
            Nombre del agente activo.
        """
        return self.data["sistema"]["agente_activo"]

    def registrar_presupuesto(self, presupuesto: float) -> None:
        """Registra el presupuesto del cliente.
        
        Args:
            presupuesto: Cantidad en soles (S/.).
        
        Raises:
            ValueError: Si el presupuesto es negativo.
        """
        if presupuesto < 0:
            raise ValueError(f"Presupuesto no puede ser negativo: {presupuesto}")
        self.data["cliente_perfil"]["presupuesto"] = round(presupuesto, 2)

    def registrar_preferencia(self, preferencia: str) -> None:
        """Registra una preferencia del cliente (sin duplicados).
        
        Args:
            preferencia: Texto descriptivo de preferencia (ej. 'Gaming', 'Trabajo')
        """
        if not preferencia or not isinstance(preferencia, str):
            raise ValueError(f"Preferencia inválida: {preferencia}")
        prefs = self.data["cliente_perfil"]["preferencias"]
        if preferencia.lower() not in [p.lower() for p in prefs]:
            prefs.append(preferencia)

    def registrar_producto_interes(self, producto: str) -> None:
        """Registra el producto de interés del cliente.
        
        Args:
            producto: Nombre o referencia del producto.
        """
        if not producto or not isinstance(producto, str):
            raise ValueError(f"Producto inválido: {producto}")
        self.data["consulta_stock"]["producto_interes"] = producto

    def registrar_marca_preferida(self, marca: str) -> None:
        """Registra la marca preferida del cliente.
        
        Args:
            marca: Nombre de la marca.
        """
        if not marca or not isinstance(marca, str):
            raise ValueError(f"Marca inválida: {marca}")
        self.data["consulta_stock"]["marca_preferida"] = marca

    def confirmar_stock(self, confirmado: bool) -> None:
        """Actualiza si el stock fue confirmado.
        
        Args:
            confirmado: True si el producto está en stock verificado.
        """
        self.data["consulta_stock"]["stock_confirmado"] = bool(confirmado)

    def informar_garantia(self, informado: bool) -> None:
        """Actualiza si la garantía fue comunicada al cliente.
        
        Args:
            informado: True si se informó sobre garantía.
        """
        self.data["consulta_stock"]["garantia_informada"] = bool(informado)

    def coordinar_entrega(self, coordinada: bool) -> None:
        """Actualiza si la entrega fue coordinada.
        
        Args:
            coordinada: True si la entrega está coordinada.
        """
        self.data["consulta_stock"]["entrega_coordinada"] = bool(coordinada)

    def to_dict(self) -> Dict[str, Any]:
        """Exporta la memoria como diccionario.
        
        Returns:
            Copia del estado interno completo.
        """
        return json.loads(json.dumps(self.data))  # Deep copy via JSON serialization

    def load_from_dict(self, source_dict: Dict[str, Any]) -> None:
        """Importa estado desde un diccionario (para recuperación de sesiones).
        
        Args:
            source_dict: Diccionario con estructura esperada.
        
        Raises:
            ValueError: Si la estructura es inválida.
        """
        if not source_dict or not isinstance(source_dict, dict):
            raise ValueError("source_dict no es un diccionario válido")
        # Validar estructura mínima
        if "cliente_perfil" in source_dict and "consulta_stock" in source_dict:
            self.data.update(source_dict)
        else:
            raise ValueError("source_dict no contiene las claves requeridas")

    def to_json_str(self) -> str:
        """Exporta la memoria como string JSON.
        
        Returns:
            String JSON formateado e indentado.
        """
        return json.dumps(self.data, indent=2, ensure_ascii=False)

    def validar_integridad(self) -> bool:
        """Valida que el estado interno sea coherente.
        
        Verifica:
        - Si garantía_informada=True, debe haber producto_interes
        - Si entrega_coordinada=True, debe haber stock_confirmado
        
        Returns:
            True si el estado es válido, False en caso contrario.
        """
        consulta = self.data.get("consulta_stock", {})
        
        # Regla 1: garantía requiere producto
        if consulta.get("garantia_informada") and not consulta.get("producto_interes"):
            return False
        
        # Regla 2: entrega requiere stock confirmado
        if consulta.get("entrega_coordinada") and not consulta.get("stock_confirmado"):
            return False
        
        return True
