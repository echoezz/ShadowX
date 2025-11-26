document.addEventListener('DOMContentLoaded', function() {
    const graphContainer = document.getElementById('transactionGraph');
    const txDetails = document.getElementById('txDetails');
    
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
                // Process and display the graph data
                renderGraph(data);
            })
            .catch(error => {
                console.error('Error fetching transaction blocks:', error);
                graphContainer.innerHTML = `<div class="text-center py-5">
                    <p class="text-danger">Error loading graph data: ${error.message}</p>
                    <p>Make sure the Monero daemon is running and has transaction data.</p>
                </div>`;
            });
    }
    
    // Function to render the graph
    function renderGraph(data) {
        console.log('Rendering graph with data:', data);
        
        if (!data || !data.nodes || data.nodes.length === 0) {
            graphContainer.innerHTML = '<div class="text-center py-5"><p>No transaction data available.</p></div>';
            return;
        }
        
        // Clear previous graph
        graphContainer.innerHTML = '';
        
        // Set up SVG dimensions
        const width = graphContainer.clientWidth;
        const height = 500;
        
        // Create SVG element
        const svg = d3.select(graphContainer)
            .append("svg")
            .attr("width", width)
            .attr("height", height)
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
        
        // Create force simulation
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(30));
        
        // Create links
        const link = g.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(data.links)
            .enter().append("line")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", 2);
        
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
        
        // Add circles to nodes
        node.append("circle")
            .attr("r", d => {
                // Size nodes based on type
                return d.type === 'transaction' ? 12 : 8;
            })
            .attr("fill", d => {
                // Color nodes based on type
                if (d.type === 'transaction') return "#4e73df";
                if (d.type === 'output') return "#1cc88a";
                if (d.type === 'input') return "#e74a3b";
                return "#858796";
            });
        
        // Add labels to nodes
        node.append("text")
            .text(d => {
                if (d.type === 'transaction') {
                    return d.id.substring(0, 8) + "..."; // Truncate transaction hash
                }
                return d.type === 'output' ? 'Out' : 'In';
            })
            .attr('x', 15)
            .attr('y', 5)
            .style("font-size", "10px");
        
        // Add titles (tooltips)
        node.append("title")
            .text(d => {
                if (d.type === 'transaction') {
                    return `Transaction: ${d.id}`;
                } else if (d.type === 'input') {
                    return `Input: ${d.id}`;
                } else {
                    return `Output: ${d.id}`;
                }
            });
        
        // Add node click handler to display details
        node.on("click", function(event, d) {
            showTransactionDetails(d);
        });
        
        // Update positions on each tick of the simulation
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node.attr("transform", d => `translate(${d.x},${d.y})`);
        });
        
        // Drag functions
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        
        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
        
        // Add legend
        const legend = svg.append("g")
            .attr("class", "legend")
            .attr("transform", "translate(20,20)");
            
        const legendData = [
            {color: "#4e73df", label: "Transaction", type: "transaction"},
            {color: "#1cc88a", label: "Output", type: "output"},
            {color: "#e74a3b", label: "Input", type: "input"}
        ];
        
        legendData.forEach((item, i) => {
            const legendRow = legend.append("g")
                .attr("transform", `translate(0, ${i * 20})`);
                
            legendRow.append("rect")
                .attr("width", 10)
                .attr("height", 10)
                .attr("fill", item.color);
                
            legendRow.append("text")
                .attr("x", 15)
                .attr("y", 10)
                .text(item.label)
                .style("font-size", "12px");
        });
    }
    
    // Function to display transaction details
    function showTransactionDetails(node) {
        const txDetails = document.getElementById('txDetails');
        
        if (node.type === 'transaction') {
            // If it's a transaction node, fetch full details
            fetch(`/api/transaction/${node.id}`)
                .then(response => response.json())
                .then(data => {
                    txDetails.innerHTML = `
                        <h5>Transaction Details</h5>
                        <p><strong>Hash:</strong> ${node.id}</p>
                        <p><strong>Block Height:</strong> ${data.block_height || 'Unknown'}</p>
                        <p><strong>Fee:</strong> ${data.fee || 'Unknown'} XMR</p>
                        <p><strong>Inputs:</strong> ${data.inputs ? data.inputs.length : 0}</p>
                        <p><strong>Outputs:</strong> ${data.outputs ? data.outputs.length : 0}</p>
                        <p><strong>Size:</strong> ${data.size || 'Unknown'} bytes</p>
                    `;
                })
                .catch(error => {
                    console.error('Error fetching transaction details:', error);
                    txDetails.innerHTML = `<p class="text-danger">Error loading transaction details: ${error.message}</p>`;
                });
        } else if (node.type === 'input' || node.type === 'output') {
            // For input/output nodes, show basic info
            txDetails.innerHTML = `
                <h5>${node.type === 'input' ? 'Input' : 'Output'} Details</h5>
                <p><strong>ID:</strong> ${node.id}</p>
                <p><strong>Type:</strong> ${node.type}</p>
            `;
        } else {
            // For other node types
            txDetails.innerHTML = `
                <h5>Node Details</h5>
                <p><strong>ID:</strong> ${node.id}</p>
                <p><strong>Type:</strong> ${node.type}</p>
            `;
        }
    }
    
    // Add event listeners for buttons
    document.getElementById('refreshData').addEventListener('click', function() {
        console.log('Refreshing data...');
        fetchTransactionBlocks();
    });
    
    document.getElementById('resetView').addEventListener('click', function() {
        const width = graphContainer.clientWidth;
        const height = 500;
        d3.select(graphContainer).select("svg")
            .transition().duration(750)
            .call(
                d3.zoom().transform,
                d3.zoomIdentity,
                d3.zoomTransform(d3.select(graphContainer).select("svg").node()).invert([width / 2, height / 2])
            );
    });
    
    document.getElementById('exportSvg').addEventListener('click', function() {
        const svg = d3.select(graphContainer).select("svg").node();
        const svgData = new XMLSerializer().serializeToString(svg);
        const svgBlob = new Blob([svgData], {type: "image/svg+xml;charset=utf-8"});
        const svgUrl = URL.createObjectURL(svgBlob);
        const downloadLink = document.createElement("a");
        downloadLink.href = svgUrl;
        downloadLink.download = "monero_transactions.svg";
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    });
    
    // Initialize by fetching data on page load
    fetchTransactionBlocks();
});