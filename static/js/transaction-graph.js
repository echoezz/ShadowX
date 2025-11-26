document.addEventListener('DOMContentLoaded', function() {
    const graphContainer = document.getElementById('transactionGraph');
    const txDetails = document.getElementById('txDetails');
    let simulation;
    let currentTxIndex = 0;
    let transactions = [];
    let fullGraphData = null; // Store the complete graph data
    
    // Helper function to format Monero amounts
    function formatMoneroAmount(atomicUnits) {
        if (atomicUnits === null || atomicUnits === undefined) return 'Unknown';
        return (atomicUnits / 1000000000000).toFixed(12) + ' XMR';
    }
    
    // Function to fetch transaction blocks data
    function fetchTransactionBlocks() {
        graphContainer.innerHTML = '<div class="text-center py-5"><p>Connecting to Monero node...</p></div>';
        
        fetch('/api/transaction-blocks/20')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Received transaction blocks data:', data);
                
                // Store the complete data for later use
                fullGraphData = data;
                
                // Extract all transaction nodes
                transactions = data.nodes.filter(node => node.type === 'transaction');
                console.log(`Found ${transactions.length} transactions`);
                
                if (transactions.length > 0) {
                    // Create navigation controls
                    createNavigationControls();
                    
                    // Show the first transaction
                    showTransactionByIndex(0);
                } else {
                    graphContainer.innerHTML = '<div class="text-center py-5"><p>No transactions found in the data.</p></div>';
                }
            })
            .catch(error => {
                console.error('Error fetching transaction blocks:', error);
                graphContainer.innerHTML = `<div class="text-center py-5">
                    <p class="text-danger">Error loading graph data: ${error.message}</p>
                    <p>Make sure the Monero daemon is running and has transaction data.</p>
                </div>`;
            });
    }
    
    // Function to create navigation controls for transactions
    function createNavigationControls() {
        // Create navigation container if it doesn't exist
        let navContainer = document.getElementById('txNavigation');
        if (!navContainer) {
            navContainer = document.createElement('div');
            navContainer.id = 'txNavigation';
            navContainer.className = 'transaction-navigation d-flex justify-content-between align-items-center mb-3';
            
            // Insert before graph container
            if (graphContainer.parentNode) {
                graphContainer.parentNode.insertBefore(navContainer, graphContainer);
            }
        } else {
            navContainer.innerHTML = '';
        }
        
        // Create previous button
        const prevBtn = document.createElement('button');
        prevBtn.className = 'btn btn-sm btn-outline-primary';
        prevBtn.innerHTML = '&larr; Previous';
        prevBtn.disabled = true; // Initially disabled
        prevBtn.addEventListener('click', () => {
            if (currentTxIndex > 0) {
                showTransactionByIndex(currentTxIndex - 1);
            }
        });
        
        // Create counter display
        const counter = document.createElement('span');
        counter.className = 'transaction-counter';
        counter.innerHTML = `Transaction <span id="current-tx">1</span> of <span id="total-tx">${transactions.length}</span>`;
        
        // Create next button
        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn btn-sm btn-outline-primary';
        nextBtn.innerHTML = 'Next &rarr;';
        nextBtn.disabled = transactions.length <= 1;
        nextBtn.addEventListener('click', () => {
            if (currentTxIndex < transactions.length - 1) {
                showTransactionByIndex(currentTxIndex + 1);
            }
        });
        
        // Add elements to nav container
        navContainer.appendChild(prevBtn);
        navContainer.appendChild(counter);
        navContainer.appendChild(nextBtn);
    }
    
    // Function to extract a subgraph for a specific transaction
    function extractTransactionSubgraph(txNode) {
        if (!fullGraphData || !txNode) return { nodes: [], links: [] };
        
        const subgraphNodes = [txNode]; // Start with the transaction node
        const subgraphLinks = [];
        const addedNodeIds = new Set([txNode.id]);
        
        // First pass: Find all directly connected nodes and links
        fullGraphData.links.forEach(link => {
            if (link.source === txNode.id || link.target === txNode.id) {
                // Find the other node ID
                const otherNodeId = link.source === txNode.id ? link.target : link.source;
                
                // Find the actual node object
                const otherNode = fullGraphData.nodes.find(node => node.id === otherNodeId);
                
                if (otherNode && !addedNodeIds.has(otherNodeId)) {
                    subgraphNodes.push(otherNode);
                    addedNodeIds.add(otherNodeId);
                }
                
                // Add the link
                subgraphLinks.push(link);
            }
        });
        
        // Second pass: For key images and inputs/outputs, include their connections
        // This ensures ring members and related entities are included
        const expandedNodeIds = new Set();
        
        subgraphNodes.forEach(node => {
            if (node.type === 'keyimage' || node.type === 'input' || node.type === 'output') {
                expandedNodeIds.add(node.id);
            }
        });
        
        // Add connections for these special nodes
        fullGraphData.links.forEach(link => {
            if (expandedNodeIds.has(link.source) || expandedNodeIds.has(link.target)) {
                // Find the other node
                const srcNodeId = link.source;
                const targetNodeId = link.target;
                
                // Add source node if not already included
                if (!addedNodeIds.has(srcNodeId)) {
                    const srcNode = fullGraphData.nodes.find(node => node.id === srcNodeId);
                    if (srcNode) {
                        subgraphNodes.push(srcNode);
                        addedNodeIds.add(srcNodeId);
                    }
                }
                
                // Add target node if not already included
                if (!addedNodeIds.has(targetNodeId)) {
                    const targetNode = fullGraphData.nodes.find(node => node.id === targetNodeId);
                    if (targetNode) {
                        subgraphNodes.push(targetNode);
                        addedNodeIds.add(targetNodeId);
                    }
                }
                
                // Add the link if not already included
                if (!subgraphLinks.some(l => l.source === link.source && l.target === link.target)) {
                    subgraphLinks.push(link);
                }
            }
        });
        
        return { nodes: subgraphNodes, links: subgraphLinks };
    }
    
    // Function to show a specific transaction by index
    function showTransactionByIndex(index) {
        if (index < 0 || index >= transactions.length) return;
        
        currentTxIndex = index;
        
        // Update counter
        const currentTxElem = document.getElementById('current-tx');
        if (currentTxElem) currentTxElem.textContent = index + 1;
        
        const totalTxElem = document.getElementById('total-tx');
        if (totalTxElem) totalTxElem.textContent = transactions.length;
        
        // Update button states
        const prevBtn = document.querySelector('#txNavigation button:first-child');
        const nextBtn = document.querySelector('#txNavigation button:last-child');
        
        if (prevBtn) prevBtn.disabled = index === 0;
        if (nextBtn) nextBtn.disabled = index === transactions.length - 1;
        
        // Get the current transaction
        const currentTx = transactions[index];
        
        // Extract subgraph data for this transaction
        const txData = extractTransactionSubgraph(currentTx);
        
        // Render the graph with just this transaction's data
        renderGraph(txData);
    }
    
    // Function to render transaction graph with all details
    function renderGraph(data) {
        console.log('Rendering graph with data:', data);
        
        if (!data || !data.nodes || data.nodes.length === 0) {
            graphContainer.innerHTML = '<div class="text-center py-5"><p>No transaction data available.</p></div>';
            return;
        }
        
        // Clear previous graph
        graphContainer.innerHTML = '';
        
        // Set up container for proper overflow handling
        graphContainer.style.overflow = "hidden";
        graphContainer.style.position = "relative";
        
        // Set up SVG dimensions
        const width = graphContainer.clientWidth;
        const height = 600;
        
        // Create SVG element with proper viewBox for scaling
        const svg = d3.select(graphContainer)
            .append("svg")
            .attr("width", "100%")
            .attr("height", height)
            .attr("viewBox", `0 0 ${width} ${height}`)
            .attr("preserveAspectRatio", "xMidYMid meet")
            .attr("class", "transaction-graph");
        
        // Create a group for zoom/pan functionality
        const g = svg.append("g");
        
        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });
        
        svg.call(zoom);
        
        // Preprocess links to ensure source and target are objects, not just IDs
        const links = data.links.map(link => {
            const source = typeof link.source === 'object' ? link.source : 
                            data.nodes.find(node => node.id === link.source);
            const target = typeof link.target === 'object' ? link.target : 
                            data.nodes.find(node => node.id === link.target);
            return {...link, source, target};
        }).filter(link => link.source && link.target); // Filter out any invalid links
        
        // Create force simulation with boundary forces
        simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(d => {
                // Set distance based on link type
                if (d.type === 'ring') return 80;
                if (d.type === 'contains') return 150;
                return 100;
            }))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("x", d3.forceX(width / 2).strength(0.05))
            .force("y", d3.forceY(height / 2).strength(0.05))
            .force("collision", d3.forceCollide().radius(d => {
                // Set collision radius based on node type
                if (d.type === 'block') return 30;
                if (d.type === 'transaction') return 25;
                if (d.type === 'keyimage') return 15;
                if (d.type === 'output') return 10;
                return 8; // ring members and others
            }));
        
        // Create links with different styles based on type
        const link = g.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("stroke", d => {
                if (d.type === 'contains') return "#36b9cc"; // block to tx links
                if (d.type === 'input') return "#e74a3b";    // input links
                if (d.type === 'output') return "#1cc88a";   // output links
                if (d.type === 'ring') return "#aaaaaa";     // ring links
                return "#858796";                           // default
            })
            .attr("class", d => d.type === 'ring' ? 'ring-line' : 'real-line')
            .attr("stroke-dasharray", d => d.type === 'ring' ? "5,5" : "0")
            .attr("stroke-width", d => {
                if (d.type === 'contains') return 2;
                if (d.type === 'input' || d.type === 'output') return 2;
                if (d.type === 'ring') return 1;
                return 1.5;
            });
        
        // Create nodes
        const node = g.append("g")
            .attr("class", "nodes")
            .selectAll("g")
            .data(data.nodes)
            .enter().append("g")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        // Add shapes to nodes based on type
        node.each(function(d) {
            const nodeElem = d3.select(this);
            
            if (d.type === 'block') {
                // Square for block nodes
                nodeElem.append("rect")
                    .attr("width", 26)
                    .attr("height", 26)
                    .attr("x", -13)
                    .attr("y", -13)
                    .attr("fill", "#36b9cc")
                    .attr("stroke", "#2c969f")
                    .attr("stroke-width", 1.5)
                    .attr("rx", 4)  // rounded corners
                    .attr("ry", 4);
            } else if (d.type === 'transaction') {
                // Circle for transaction nodes
                nodeElem.append("circle")
                    .attr("r", 12)
                    .attr("fill", "#4e73df")
                    .attr("stroke", "#2653cf")
                    .attr("stroke-width", 1.5);
            } else if (d.type === 'keyimage') {
                // Diamond for key image nodes
                nodeElem.append("polygon")
                    .attr("points", "0,-10 10,0 0,10 -10,0")
                    .attr("fill", "#f6c23e")
                    .attr("stroke", "#dda20a")
                    .attr("stroke-width", 1.5);
            } else if (d.type === 'ring_member') {
                // Small circle for decoy/ring member nodes
                nodeElem.append("circle")
                    .attr("r", 5)
                    .attr("fill", "#858796")
                    .attr("stroke", "#636470")
                    .attr("stroke-width", 1);
            } else if (d.type === 'output') {
                // Circle for output nodes
                nodeElem.append("circle")
                    .attr("r", 8)
                    .attr("fill", "#1cc88a")
                    .attr("stroke", "#13855c")
                    .attr("stroke-width", 1.5);
            } else if (d.type === 'input') {
                // Circle for input nodes
                nodeElem.append("circle")
                    .attr("r", 8)
                    .attr("fill", "#e74a3b")
                    .attr("stroke", "#be2617")
                    .attr("stroke-width", 1.5);
            } else {
                // Default circle for other nodes
                nodeElem.append("circle")
                    .attr("r", 6)
                    .attr("fill", "#858796")
                    .attr("stroke", "#636470")
                    .attr("stroke-width", 1);
            }
        });
        
        // Add labels to nodes
        node.append("text")
            .text(d => {
                if (d.type === 'block') return 'b:' + d.height;
                if (d.type === 'transaction') return 'tx:' + d.hash.substring(0, 6);
                if (d.type === 'keyimage') return 'ki:' + (d.key_image ? d.key_image.substring(0, 6) : '');
                if (d.type === 'ring_member') return 'r:' + d.absolute_offset;
                if (d.type === 'output') return 'o:' + d.index;
                if (d.type === 'input') return 'in:' + d.input_index;
                return d.id ? d.id.substring(0, 6) : '';
            })
            .attr('x', d => {
                // Position labels based on node type
                if (d.type === 'block') return 15;
                if (d.type === 'transaction') return 15;
                if (d.type === 'keyimage') return 12;
                return 8;
            })
            .attr('y', 5)
            .style("font-size", "10px")
            .style("pointer-events", "none");  // Make text not interfere with clicks
        
        // Add node click handler to display details
        node.on("click", function(event, d) {
            // Reset all nodes to normal appearance
            node.selectAll("circle, rect, polygon")
                .attr("stroke-width", d => d.type === 'ring_member' ? 1 : 1.5);
            
            // Highlight clicked node
            d3.select(this).select("circle, rect, polygon")
                .attr("stroke-width", 3);
                
            showNodeDetails(d);
            
            // Prevent event from bubbling up
            event.stopPropagation();
        });
        
        // Clear details when clicking on the background
        svg.on("click", function(event) {
            if (event.target === this) {
                txDetails.innerHTML = '<p class="text-center">Select a transaction node to view details.</p>';
                // Reset all nodes to normal appearance
                node.selectAll("circle, rect, polygon")
                    .attr("stroke-width", d => d.type === 'ring_member' ? 1 : 1.5);
            }
        });
        
        // Update positions on each tick of the simulation with boundary enforcement
        simulation.on("tick", () => {
            // Enforce boundaries for all nodes
            data.nodes.forEach(d => {
                const radius = d.type === 'transaction' ? 12 : 
                              d.type === 'block' ? 13 : 
                              d.type === 'keyimage' ? 10 : 8;
                              
                d.x = Math.max(radius, Math.min(width - radius, d.x));
                d.y = Math.max(radius, Math.min(height - radius, d.y));
            });
            
            // Update link positions
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            // Update node positions
            node.attr("transform", d => `translate(${d.x},${d.y})`);
        });
        
        // Drag functions
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            // Keep the dragged position within boundaries
            const radius = d.type === 'transaction' ? 12 : 
                          d.type === 'block' ? 13 : 
                          d.type === 'keyimage' ? 10 : 8;
                          
            d.fx = Math.max(radius, Math.min(width - radius, event.x));
            d.fy = Math.max(radius, Math.min(height - radius, event.y));
        }
        
        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
    }
    
    // Function to show node details
    function showNodeDetails(node) {
        console.log("Showing details for node:", node);
        
        if (node.type === 'block') {
            txDetails.innerHTML = `
                <h5>Block Details</h5>
                <p><strong>Height:</strong> ${node.height || 'Unknown'}</p>
                <p><strong>Hash:</strong> ${node.hash || 'Unknown'}</p>
                <p><strong>Timestamp:</strong> ${formatTimestamp(node.timestamp)}</p>
                <p><strong>Transaction Count:</strong> ${node.tx_count || 0}</p>
            `;
        } else if (node.type === 'transaction') {
            // Get transaction details from the node
            const details = node.details || {};
            
            txDetails.innerHTML = `
                <h5>Transaction Details</h5>
                <p><strong>Hash:</strong> ${node.hash || 'Unknown'}</p>
                <p><strong>Block Height:</strong> ${node.block_height !== undefined ? node.block_height : 'Unknown'}</p>
                <p><strong>Fee:</strong> ${formatMoneroAmount(details.fee)}</p>
                <p><strong>Inputs:</strong> ${details.inputs !== undefined ? details.inputs : 'Unknown'}</p>
                <p><strong>Outputs:</strong> ${details.outputs !== undefined ? details.outputs : 'Unknown'}</p>
                <p><strong>Size:</strong> ${details.size ? details.size + ' bytes' : 'Unknown'}</p>
                <p><strong>Version:</strong> ${details.version !== undefined ? details.version : 'Unknown'}</p>
            `;
        } else if (node.type === 'keyimage') {
            txDetails.innerHTML = `
                <h5>Key Image Details</h5>
                <p><strong>Key Image:</strong> ${node.key_image || 'Unknown'}</p>
                <p><strong>Input Index:</strong> ${node.input_index !== undefined ? node.input_index : 'Unknown'}</p>
                <p><strong>This represents one of the inputs being spent in this transaction.</strong></p>
            `;
        } else if (node.type === 'ring_member') {
            txDetails.innerHTML = `
                <h5>Ring Member</h5>
                <p><strong>Output offset:</strong> ${node.absolute_offset || 'Unknown'}</p>
                <p class="text-muted">This is a potential input source in the ring signature.</p>
                <p class="text-muted">Only one member of the ring is the real input being spent.</p>
            `;
        } else if (node.type === 'output') {
            txDetails.innerHTML = `
                <h5>Output Details</h5>
                <p><strong>Index:</strong> ${node.index !== undefined ? node.index : 'Unknown'}</p>
                <p><strong>Amount:</strong> ${formatMoneroAmount(node.amount)}</p>
                <p class="text-muted">This output can be spent in future transactions.</p>
            `;
        } else if (node.type === 'input') {
            txDetails.innerHTML = `
                <h5>Input Details</h5>
                <p><strong>Key Image:</strong> ${node.key_image || 'Unknown'}</p>
                <p class="text-muted">This input is being spent in the transaction.</p>
            `;
        }
    }
    
    // Helper function to format timestamps
    function formatTimestamp(timestamp) {
        if (!timestamp) return 'Unknown';
        const date = new Date(timestamp * 1000);
        return date.toLocaleString();
    }
    
    // Add event listeners for buttons
    const refreshBtn = document.getElementById('refreshData');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            fetchTransactionBlocks();
        });
    }
    
    const resetBtn = document.getElementById('resetView');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            if (simulation) {
                simulation.stop();
            }
            
            const svg = d3.select(graphContainer).select("svg");
            if (!svg.empty()) {
                svg.transition().duration(750).call(
                    d3.zoom().transform,
                    d3.zoomIdentity
                );
            }
            
            // Reset to default view
            fetchTransactionBlocks();
        });
    }
    
    const exportBtn = document.getElementById('exportSvg');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            const svg = d3.select(graphContainer).select("svg").node();
            if (!svg) {
                alert("No graph to export");
                return;
            }
            
            const svgData = new XMLSerializer().serializeToString(svg);
            const svgBlob = new Blob([svgData], {type: "image/svg+xml;charset=utf-8"});
            const svgUrl = URL.createObjectURL(svgBlob);
            const downloadLink = document.createElement("a");
            downloadLink.href = svgUrl;
            downloadLink.download = "monero_transaction.svg";
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            URL.revokeObjectURL(svgUrl);
        });
    }
    
    // Initialize by fetching transaction blocks
    fetchTransactionBlocks();
});