import { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';
import { ArrowLeft, Folder, FileText, Box } from 'lucide-react';

const ObjectView = ({ oid, type, onBack, onNavigate }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        setLoading(true);
        const endpoint = type === 'tree' ? `${API_URL}/api/tree/${oid}` : `${API_URL}/api/blob/${oid}`;
        axios.get(endpoint)
            .then(res => setData(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [oid, type]);

    if (loading) return <div style={{ padding: '1rem' }}>Loading object...</div>;
    if (!data) return <div style={{ padding: '1rem', color: 'red' }}>Error loading object.</div>;

    return (
        <div style={{ padding: '0.5rem' }}>
            <button
                onClick={onBack}
                className="btn"
                style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
                <ArrowLeft size={16} /> Back
            </button>

            <div style={{ marginBottom: '1rem' }}>
                <span className="badge" style={{ textTransform: 'uppercase', fontSize: '0.7rem' }}>{type}</span>
                <div style={{ fontFamily: 'monospace', wordBreak: 'break-all', fontSize: '0.9rem', marginTop: '0.25rem' }}>
                    {oid}
                </div>
            </div>

            {type === 'tree' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {data.map((entry, i) => (
                        <div
                            key={i}
                            className="card hover-effect"
                            style={{
                                padding: '0.75rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.75rem',
                                cursor: 'pointer',
                                transition: 'background-color 0.2s'
                            }}
                            onClick={() => onNavigate(entry.oid, entry.type)}
                        >
                            {entry.type === 'tree' ? <Folder size={18} color="var(--accent)" /> : <FileText size={18} color="var(--text-secondary)" />}
                            <div style={{ flex: 1, overflow: 'hidden' }}>
                                <div style={{ fontWeight: '500', truncate: true }}>{entry.name}</div>
                                <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                                    {entry.mode} • {entry.oid.slice(0, 7)}
                                </div>
                            </div>
                            <button className="btn" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}>
                                Inspect
                            </button>
                        </div>
                    ))}
                    {data.length === 0 && <p style={{ color: 'var(--text-secondary)' }}>Empty tree</p>}
                </div>
            ) : (
                <div className="card" style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
                        <FileText size={20} color="var(--accent)" />
                        <span style={{ fontWeight: '600' }}>Blob Content</span>
                        <span className="badge">{data.size} bytes</span>
                    </div>

                    {data.content === "<Binary Data>" ? (
                        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                            <Box size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
                            <p>Binary Content</p>
                        </div>
                    ) : (
                        <pre style={{
                            background: 'var(--bg-primary)',
                            padding: '1rem',
                            borderRadius: '4px',
                            overflowX: 'auto',
                            fontFamily: 'monospace',
                            fontSize: '0.9rem',
                            margin: 0
                        }}>
                            {data.content}
                        </pre>
                    )}
                </div>
            )}
        </div>
    );
};

export default ObjectView;
