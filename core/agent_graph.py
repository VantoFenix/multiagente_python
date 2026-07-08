"""
agent_graph.py — Grafo de topología de agentes (Agent Graph).

Define la red de delegación jerárquica entre agentes especializados
con transiciones permitidas y condiciones asociadas.
"""

from typing import Dict, Optional, Any
from .agent import Agent


class AgentNode:
    """Nodo en el grafo de agentes.
    
    Attributes:
        agent: Instancia del agente.
        connections: Diccionario de transiciones permitidas (destino -> condición).
    """
    
    def __init__(self, agent: Agent) -> None:
        """Inicializa un nodo de agente.
        
        Args:
            agent: Instancia del agente a encapsular.
        """
        self.agent = agent
        self.connections: Dict[str, str] = {}


class AgentGraph:
    """Grafo dirigido de delegación entre agentes multiagente.
    
    Proporciona:
    - Registro de agentes como nodos
    - Definición de transiciones permitidas con condiciones
    - Validación de topología
    - Introspección del grafo
    """
    
    def __init__(self) -> None:
        """Inicializa el grafo vacío."""
        self.nodes: Dict[str, AgentNode] = {}

    def add_agent(self, agent: Agent) -> None:
        """Agrega un nodo de agente al grafo.
        
        Args:
            agent: Instancia del agente a registrar.
        
        Raises:
            ValueError: Si agent es None o el nombre ya existe.
        """
        if agent is None:
            raise ValueError("agent no puede ser None")
        if agent.name in self.nodes:
            raise ValueError(f"Agente '{agent.name}' ya registrado en el grafo")
        
        self.nodes[agent.name] = AgentNode(agent)

    def add_transition(self, from_agent_name: str, to_agent_name: str, 
                      condition_desc: str = "") -> None:
        """Agrega una arista (transición permitida) entre dos agentes.
        
        Args:
            from_agent_name: Nombre del agente origen.
            to_agent_name: Nombre del agente destino.
            condition_desc: Descripción de la condición de transición.
        
        Raises:
            KeyError: Si alguno de los agentes no existe en el grafo.
            ValueError: Si los nombres son inválidos.
        """
        if not from_agent_name or not isinstance(from_agent_name, str):
            raise ValueError(f"from_agent_name inválido: {from_agent_name}")
        if not to_agent_name or not isinstance(to_agent_name, str):
            raise ValueError(f"to_agent_name inválido: {to_agent_name}")
        
        if from_agent_name not in self.nodes:
            raise KeyError(f"Agente origen no existe: {from_agent_name}")
        if to_agent_name not in self.nodes:
            raise KeyError(f"Agente destino no existe: {to_agent_name}")
        
        self.nodes[from_agent_name].connections[to_agent_name] = condition_desc or ""

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """Obtiene la instancia del agente por nombre.
        
        Args:
            agent_name: Nombre del agente.
        
        Returns:
            Instancia del agente o None si no existe.
        """
        if agent_name not in self.nodes:
            return None
        return self.nodes[agent_name].agent

    def get_transitions(self, agent_name: str) -> Dict[str, str]:
        """Obtiene las transiciones de salida permitidas para un agente.
        
        Args:
            agent_name: Nombre del agente.
        
        Returns:
            Diccionario {agente_destino -> condición_desc} o {} si no existe.
        """
        if agent_name not in self.nodes:
            return {}
        return self.nodes[agent_name].connections.copy()

    def agent_exists(self, agent_name: str) -> bool:
        """Verifica si un agente existe en el grafo.
        
        Args:
            agent_name: Nombre del agente.
        
        Returns:
            True si existe, False en caso contrario.
        """
        return agent_name in self.nodes

    def get_all_agents(self) -> Dict[str, Agent]:
        """Retorna todos los agentes del grafo.
        
        Returns:
            Diccionario {nombre -> instancia_agente}.
        """
        return {name: node.agent for name, node in self.nodes.items()}

    def print_topology(self) -> None:
        """Imprime la topología del grafo en consola."""
        print("\n" + "=" * 65)
        print("          TOPOLOGÍA DE RED MULTIAGENTE (AGENT GRAPH)")
        print("=" * 65)
        for name, node in self.nodes.items():
            print(f"  Nodo Agent: [{name}]")
            if node.connections:
                for target, cond in node.connections.items():
                    condition_text = f" | Condición: \"{cond}\"" if cond else ""
                    print(f"    --> Delegación a: [{target}]{condition_text}")
            else:
                print(f"    (sin transiciones de salida)")
        print("=" * 65 + "\n")
