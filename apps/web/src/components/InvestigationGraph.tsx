"use client";

import React, { useMemo } from "react";
import ReactFlow, { Background, Controls, Node, Edge } from "reactflow";
import "reactflow/dist/style.css";

interface Relationship {
  id: string;
  source_entity_type: string;
  source_entity_id: string;
  target_entity_type: string;
  target_entity_id: string;
  relationship_type: string;
}

export default function InvestigationGraph({ relationships }: { relationships: Relationship[] }) {
  const { nodes, edges } = useMemo(() => {
    const initialNodes: Node[] = [
      {
        id: "TX-18492",
        position: { x: 250, y: 150 },
        data: { label: <div><strong>TX-18492</strong><br/>₹2,84,000</div> },
        style: { background: '#1e1e1e', color: 'white', border: '1px solid #333' }
      },
      {
        id: "CUST-1042",
        position: { x: 50, y: 150 },
        data: { label: <div><strong>CUSTOMER</strong><br/>CUST-1042</div> },
        style: { background: '#1e1e1e', color: 'white', border: '1px solid #333' }
      }
    ];

    const initialEdges: Edge[] = [
      { id: "e-cust-tx", source: "CUST-1042", target: "TX-18492", label: "initiated", animated: true }
    ];

    relationships.forEach((rel, index) => {
      // Dynamic positioning based on target type
      let x = 450;
      let y = 50 + (index * 100);
      let bg = '#1e1e1e';
      let border = '1px solid #333';
      
      if (rel.target_entity_type === "IP_ADDRESS") {
        x = 250; y = 20; border = '1px solid #ef4444'; // Red for suspicious
      }
      if (rel.target_entity_type === "ALERT") {
        x = 250; y = -80; border = '1px solid #ef4444'; bg = '#ef4444'; 
      }
      if (rel.target_entity_type === "LOCATION") {
        x = 450; y = 150; border = '1px solid #eab308'; // Yellow for anomaly
      }

      initialNodes.push({
        id: rel.target_entity_id,
        position: { x, y },
        data: { label: <div><strong>{rel.target_entity_type}</strong><br/>{rel.target_entity_id}</div> },
        style: { background: bg, color: 'white', border: border }
      });

      initialEdges.push({
        id: `e-${rel.id}`,
        source: rel.source_entity_id,
        target: rel.target_entity_id,
        label: rel.relationship_type,
        animated: true,
        style: { stroke: '#666' }
      });
    });

    return { nodes: initialNodes, edges: initialEdges };
  }, [relationships]);

  return (
    <div style={{ height: "100%", width: "100%" }}>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background color="#333" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
