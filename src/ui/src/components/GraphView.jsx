
import { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import axios from 'axios';
import { API_URL } from '../config';

const GraphView = ({ onNodeClick, refreshTrigger }) => {
    const [data, setData] = useState({ nodes: [], edges: [] });
    const [dimensions, setDimensions] = useState({ w: 800, h: 600 });
    const containerRef = useRef(null);
    const fgRef = useRef();

    useEffect(() => {
        // Resize observer
        const updateSize = () => {
            if (containerRef.current) {
                setDimensions({
                    w: containerRef.current.offsetWidth,
                    h: containerRef.current.offsetHeight
                });
            }
        };

        // Use ResizeObserver to detect container size changes (e.g. sidebar open)
        const observer = new ResizeObserver(updateSize);
        if (containerRef.current) {
            observer.observe(containerRef.current);
        }

        updateSize();

        // Fetch Data
        const fetchData = () => {
            axios.get(`${API_URL}/api/graph`).then(res => {
                // Process data for ForceGraph
                // It expects 'links' instead of 'edges' and objects/ids
                const nodes = res.data.nodes.map(n => ({
                    ...n,
                    val: 5 // circle size
                }));
                const links = res.data.edges.map(e => ({
                    source: e.source,
                    target: e.target
                }));

                setData({ nodes, links });
            }).catch(console.error);
        };
        fetchData();

        return () => observer.disconnect();
    }, [refreshTrigger]);

    if (data.nodes.length === 0) {
        return (
            <div style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                color: 'var(--text-secondary)'
            }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
                <h2 style={{ color: 'var(--text-primary)' }}>Repository is Empty</h2>
                <p>Create your first commit using the controls above.</p>
            </div>
        );
    }

    return (
        <div ref={containerRef} style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
            <ForceGraph2D
                ref={fgRef}
                width={dimensions.w}
                height={dimensions.h}
                graphData={data}

                // Ensure free 2D movement (no DAG constraints)
                dagMode={null}
                // Custom rendering to show info inside node
                nodeCanvasObject={(node, ctx, globalScale) => {
                    const label = node.message || node.id;
                    const fontSize = 12 / globalScale;
                    ctx.font = `${fontSize}px Sans-Serif`;

                    // Box dimensions
                    const textWidth = ctx.measureText(label).width;
                    const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2); // some padding

                    // Draw Rect
                    ctx.fillStyle = node.group === 'commit' ? '#1e293b' : '#ef4444';
                    if (node.group === 'commit') {
                        // Draw a nice card
                        const w = 60;
                        const h = 25;

                        // Card Background
                        ctx.fillStyle = '#1e293b';
                        ctx.strokeStyle = '#3b82f6';
                        ctx.lineWidth = 0.5;
                        ctx.beginPath();
                        ctx.roundRect(node.x - w / 2, node.y - h / 2, w, h, 2);
                        ctx.fill();
                        ctx.stroke();

                        // Text: OID
                        ctx.fillStyle = '#94a3b8';
                        ctx.font = `3px sans-serif`;
                        ctx.textAlign = 'left';
                        ctx.fillText(node.id.slice(0, 7), node.x - w / 2 + 2, node.y - h / 2 + 5);

                        // Text: Message
                        ctx.fillStyle = '#f8fafc';
                        ctx.font = `4px sans-serif`; // bigger title
                        const msg = node.message.length > 20 ? node.message.slice(0, 20) + '...' : node.message;
                        ctx.fillText(msg, node.x - w / 2 + 2, node.y - h / 2 + 10);

                        // Text: Author
                        ctx.fillStyle = '#64748b';
                        ctx.font = `2px sans-serif`;
                        const authorName = node.author.split('<')[0].trim();
                        ctx.fillText(authorName, node.x - w / 2 + 2, node.y - h / 2 + 16);

                    } else {
                        // Fallback for non-commits
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
                        ctx.fill();
                    }
                }}
                nodePointerAreaPaint={(node, color, ctx) => {
                    const w = 60;
                    const h = 25;
                    ctx.fillStyle = color;
                    ctx.beginPath();
                    ctx.roundRect(node.x - w / 2, node.y - h / 2, w, h, 2);
                    ctx.fill();
                }}

                // Arrow styling - make them more visible
                linkDirectionalArrowLength={6}
                linkDirectionalArrowRelPos={1}
                linkDirectionalArrowColor={() => '#3b82f6'}
                linkColor={() => '#3b82f6'}
                linkWidth={2}
                linkDirectionalParticles={2}
                linkDirectionalParticleWidth={2}
                linkDirectionalParticleSpeed={0.005}

                onNodeClick={onNodeClick}
                backgroundColor="#0f172a"

                // Enable smooth dragging with beautiful animations
                enableNodeDrag={true}
                d3AlphaDecay={0.02}  // Slower decay = smoother settling
                d3VelocityDecay={0.3}  // Smooth deceleration

                // Fix node position after dragging
                onNodeDragEnd={node => {
                    node.fx = node.x;
                    node.fy = node.y;
                }}

                // Smooth zoom interactions
                enableZoomInteraction={true}

                // Improve stability and smoothness
                cooldownTicks={100}
                onEngineStop={() => { }}
                warmupTicks={100}

                // Keep nodes centered and prevent flying off
                d3Force={{
                    charge: { strength: -120 },
                    center: { x: dimensions.w / 2, y: dimensions.h / 2, strength: 0.05 },
                    collision: { radius: 35 }
                }}
            />
        </div>
    );
};

export default GraphView;
