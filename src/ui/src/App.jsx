import { useState, useEffect } from 'react';
import axios from 'axios';
import { GitGraph, Box, FileText, X } from 'lucide-react';
import GraphView from './components/GraphView';
import ObjectView from './components/ObjectView';
import { API_URL } from './config';
import './index.css';

function App() {
  const [selectedNode, setSelectedNode] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [viewingObject, setViewingObject] = useState(null); // { oid, type }
  const [history, setHistory] = useState([]); // For back navigation
  const [branches, setBranches] = useState([]);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [commitMessage, setCommitMessage] = useState('');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // ... existing code ...

  const handleNavigate = (oid, type) => {
    // Add current object to history
    if (viewingObject) {
      setHistory(prev => [...prev, viewingObject]);
    }
    setViewingObject({ oid, type });
  };

  const handleBack = () => {
    if (history.length > 0) {
      const prev = history[history.length - 1];
      setHistory(prevHist => prevHist.slice(0, -1));
      setViewingObject(prev);
    } else {
      setViewingObject(null);
    }
  };

  // ... render ...

  {
    viewingObject ? (
      <ObjectView
        oid={viewingObject.oid}
        type={viewingObject.type}
        onBack={handleBack}
        onNavigate={handleNavigate}
      />
    ) : selectedNode ? (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div className="card">
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Message</span>
          <p style={{ margin: '0.5rem 0', fontWeight: '500' }}>{selectedNode.message}</p>
        </div>

        <div className="card">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>OID</span>
              <div style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>{selectedNode.oid}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Author</span>
              <div>{selectedNode.author}</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Tree OID</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
                <Box size={16} color="var(--accent)" />
                <span style={{ fontFamily: 'monospace' }}>{selectedNode.tree_oid?.slice(0, 7)}...</span>
              </div>
            </div>
            <button
              className="btn"
              style={{ fontSize: '0.8rem' }}
              onClick={() => setViewingObject({ oid: selectedNode.tree_oid, type: 'tree' })}
            >
              Inspect Internals
            </button>
          </div>
        </div>

        {selectedNode.parent_oids && selectedNode.parent_oids.length > 0 && (
          <div className="card">
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Parents</span>
            <ul style={{ margin: '0.5rem 0', paddingLeft: '1.2rem', fontFamily: 'monospace' }}>
              {selectedNode.parent_oids.map(p => (
                <li key={p}>{p.slice(0, 7)}...</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    ) : (
      <p>Loading...</p>
    )
  }

  useEffect(() => {
    // Initial fetch handled by GraphView
  }, []);

  useEffect(() => {
    // Trigger graph refresh
  }, [refreshTrigger]);

  // Actually we need to know the current branch to show in the dropdown.
  // I'll add a quick HEAD endpoint logic or just rely on the user switching. 
  const handleCreateCommit = () => {
    if (!commitMessage) return;
    axios.post(`${API_URL}/api/commits`, { message: commitMessage })
      .then(() => {
        setCreateModalOpen(false);
        setCommitMessage('');
        setRefreshTrigger(prev => prev + 1);
      })
      .catch(console.error);
  };

  const handleNodeClick = (node) => {
    // 1. Instant feedback: Show what we know from the graph node
    // The graph node has 'label', 'id'.
    // We can show a loading state in the sidebar immediately.
    setSelectedNode({
      oid: node.id,
      message: "Loading details...",
      author: "...",
      tree_oid: "..."
    });
    setSidebarOpen(true);

    // 2. Fetch full details
    axios.get(`${API_URL}/api/commits/${node.id}`).then(res => {
      setSelectedNode(res.data);
    }).catch(e => {
      console.error(e);
      // Optional: show error state in selectedNode
      setSelectedNode(prev => ({ ...prev, message: "Error loading details." }));
    });
  };

  return (
    <>
      <header style={{
        height: '60px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 2rem',
        background: 'var(--bg-secondary)',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <GitGraph color="var(--accent)" />
          <h1 style={{ fontSize: '1.25rem', fontWeight: '600' }}>Git Graph Explorer</h1>
        </div>

        <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
          <button className="btn" style={{ background: 'var(--accent)', borderColor: 'var(--accent)', color: '#fff' }} onClick={() => setCreateModalOpen(true)}>
            + Commit
          </button>
          {/* Seed Demo button removed */}
          {/* Reset button removed */}
        </div>
      </header>

      <main style={{ flex: 1, position: 'relative', display: 'flex' }}>
        <div style={{ flex: 1 }}>
          <GraphView onNodeClick={handleNodeClick} refreshTrigger={refreshTrigger} />
        </div>

        {/* Commit Modal */}
        {createModalOpen && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
          }}>
            <div className="card" style={{ width: '400px', background: 'var(--bg-secondary)' }}>
              <h2 style={{ marginTop: 0 }}>Create Commit</h2>
              <input
                type="text"
                placeholder="Commit Message"
                className="card"
                style={{ width: '90%', marginBottom: '1rem', background: 'var(--bg-primary)', color: 'white' }}
                value={commitMessage}
                onChange={e => setCommitMessage(e.target.value)}
                autoFocus
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button className="btn" onClick={() => setCreateModalOpen(false)}>Cancel</button>
                <button className="btn" style={{ background: 'var(--accent)', borderColor: 'var(--accent)', color: 'white' }} onClick={() => {
                  if (!commitMessage) return;
                  axios.post(`${API_URL}/api/commits`, { message: commitMessage })
                    .then((res) => {
                      setCreateModalOpen(false);
                      setCommitMessage('');
                      setRefreshTrigger(prev => prev + 1);
                      // Show details logic could go here, for now using alert to be simple and direct
                      alert(`Commit Created!\n\nCommit SHA: ${res.data.oid}\nTree SHA: ${res.data.tree_oid}\nParent: ${res.data.parent_oids[0] || 'None'}`);
                    })
                    .catch(console.error);
                }}>Create</button>
              </div>
            </div>
          </div>
        )}

        {/* Branch Modal Removed */}

        {sidebarOpen && (
          <aside style={{
            width: '400px',
            background: 'var(--bg-secondary)',
            borderLeft: '1px solid var(--border)',
            padding: '1.5rem',
            overflowY: 'auto',
            // Made relative (flex item) so graph shrinks
            boxShadow: '-4px 0 15px rgba(0,0,0,0.3)',
            zIndex: 10
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.2rem', margin: 0 }}>Commit Details</h2>
              <button
                onClick={() => setSidebarOpen(false)}
                className="btn"
                style={{ padding: '0.25rem' }}
              >
                <X size={18} />
              </button>
            </div>

            {viewingObject ? (
              <ObjectView
                oid={viewingObject.oid}
                type={viewingObject.type}
                onBack={handleBack}
                onNavigate={handleNavigate}
              />
            ) : selectedNode ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div className="card">
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Message</span>
                  <p style={{ margin: '0.5rem 0', fontWeight: '500' }}>{selectedNode.message}</p>
                </div>

                <div className="card">
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <div>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>OID</span>
                      <div style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>{selectedNode.oid}</div>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Author</span>
                      <div>{selectedNode.author}</div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Tree OID</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
                        <Box size={16} color="var(--accent)" />
                        <span style={{ fontFamily: 'monospace' }}>{selectedNode.tree_oid?.slice(0, 7)}...</span>
                      </div>
                    </div>
                    <button
                      className="btn"
                      style={{ fontSize: '0.8rem' }}
                      onClick={() => setViewingObject({ oid: selectedNode.tree_oid, type: 'tree' })}
                    >
                      Inspect Internals
                    </button>
                  </div>
                </div>

                {selectedNode.parent_oids && selectedNode.parent_oids.length > 0 && (
                  <div className="card">
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Parents</span>
                    <ul style={{ margin: '0.5rem 0', paddingLeft: '1.2rem', fontFamily: 'monospace' }}>
                      {selectedNode.parent_oids.map(p => (
                        <li key={p}>{p.slice(0, 7)}...</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p>Loading...</p>
            )}
          </aside>
        )}
      </main>
    </>
  );
}

export default App;
