/*
   Schwerpunkt Stock Terminal Wrapper
   Interactive Client-side HTML5 Canvas Charting Engine
*/

class StockChart {
    constructor(canvas, data, options = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.data = data; // Array of {date: "YYYY-MM-DD", close: float, volume: int}
        this.options = Object.assign({
            primaryColor: '#3b5998',  // Classic Facebook Blue
            gridColor: '#e9ebee',     // Web 2.0 Light Gray Grid
            borderColor: '#ccd6e8',   // Blueish border
            textColor: '#555555',     // Axis label gray
            hoverColor: '#6d84b4',    // Hover line color
            selectionColor: 'rgba(59, 89, 152, 0.12)',
            lineWidth: 2,
            markerSize: 4,
            isIndex: false
        }, options);

        this.padding = { top: 30, right: 20, bottom: 40, left: 55 };
        this.hoverIndex = -1;
        
        // Drag-to-measure percentage change states
        this.isDragging = false;
        this.dragStartIndex = -1;
        this.dragEndIndex = -1;
        this.dragStartX = 0;
        this.dragCurrentX = 0;
        this.dragTimeout = null;

        this.init();
    }

    setupCanvas() {
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();
        
        // Set actual resolution matching the DPI
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        
        // Scale back the context drawing so coordinate maths use CSS pixels
        this.ctx.scale(dpr, dpr);
        this.width = rect.width;
        this.height = rect.height;
    }

    calculateScale() {
        if (!this.data || this.data.length === 0) return;
        
        this.prices = this.data.map(d => d.close);
        this.minPrice = Math.min(...this.prices);
        this.maxPrice = Math.max(...this.prices);
        
        const priceDiff = this.maxPrice - this.minPrice;
        const verticalPadding = priceDiff > 0 ? priceDiff * 0.08 : 1.0;
        
        this.minPrice = Math.max(0, this.minPrice - verticalPadding);
        this.maxPrice = this.maxPrice + verticalPadding;
        
        this.plotWidth = this.width - this.padding.left - this.padding.right;
        this.plotHeight = this.height - this.padding.top - this.padding.bottom;
    }

    getX(index) {
        if (this.data.length <= 1) return this.padding.left;
        return this.padding.left + (index / (this.data.length - 1)) * this.plotWidth;
    }

    getY(price) {
        if (this.maxPrice === this.minPrice) return this.padding.top + this.plotHeight / 2;
        const pct = (price - this.minPrice) / (this.maxPrice - this.minPrice);
        return this.padding.top + this.plotHeight - (pct * this.plotHeight);
    }

    drawGridAndAxes() {
        // Draw main bounding axes
        this.ctx.strokeStyle = this.options.borderColor;
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.moveTo(this.padding.left, this.padding.top);
        this.ctx.lineTo(this.padding.left, this.height - this.padding.bottom);
        this.ctx.lineTo(this.width - this.padding.right, this.height - this.padding.bottom);
        this.ctx.stroke();

        // Draw horizontal gridlines & Y price ticks (5 ticks)
        const ticksCount = 5;
        this.ctx.fillStyle = this.options.textColor;
        this.ctx.font = '9px Tahoma, sans-serif';
        this.ctx.textAlign = 'right';
        this.ctx.textBaseline = 'middle';
        
        for (let i = 0; i < ticksCount; i++) {
            const price = this.minPrice + (i / (ticksCount - 1)) * (this.maxPrice - this.minPrice);
            const y = this.getY(price);
            
            // Draw grid line
            this.ctx.strokeStyle = this.options.gridColor;
            this.ctx.beginPath();
            this.ctx.moveTo(this.padding.left, y);
            this.ctx.lineTo(this.width - this.padding.right, y);
            this.ctx.stroke();
            
            // Price Label
            this.ctx.fillStyle = this.options.textColor;
            this.ctx.fillText(`$${price.toFixed(2)}`, this.padding.left - 6, y);
        }

        // Draw date gridlines & X axis ticks (4 ticks)
        const dateTicksCount = 4;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'top';
        const dateStride = Math.max(1, Math.floor(this.data.length / dateTicksCount));
        
        for (let i = 0; i < dateTicksCount; i++) {
            const index = Math.min(this.data.length - 1, i * dateStride);
            if (index < 0) continue;
            
            const x = this.getX(index);
            const item = this.data[index];
            
            // Draw grid line
            this.ctx.strokeStyle = this.options.gridColor;
            this.ctx.beginPath();
            this.ctx.moveTo(x, this.padding.top);
            this.ctx.lineTo(x, this.height - this.padding.bottom);
            this.ctx.stroke();

            // Date text (e.g. YYYY-MM-DD)
            this.ctx.fillStyle = this.options.textColor;
            this.ctx.fillText(item.date, x, this.height - this.padding.bottom + 6);
        }
    }

    drawLine() {
        this.ctx.strokeStyle = this.options.primaryColor;
        this.ctx.lineWidth = this.options.lineWidth;
        this.ctx.beginPath();
        
        for (let i = 0; i < this.data.length; i++) {
            const x = this.getX(i);
            const y = this.getY(this.data[i].close);
            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }
        this.ctx.stroke();

        // Draw vintage square line markers at intervals
        const markerInterval = Math.max(1, Math.floor(this.data.length / 45));
        this.ctx.fillStyle = this.options.primaryColor;
        for (let i = 0; i < this.data.length; i += markerInterval) {
            const x = this.getX(i);
            const y = this.getY(this.data[i].close);
            this.ctx.fillRect(
                x - this.options.markerSize / 2, 
                y - this.options.markerSize / 2, 
                this.options.markerSize, 
                this.options.markerSize
            );
        }
    }

    drawHoverGuide() {
        const item = this.data[this.hoverIndex];
        const x = this.getX(this.hoverIndex);
        const y = this.getY(item.close);

        // Vertical dashed tracker line
        this.ctx.strokeStyle = this.options.hoverColor;
        this.ctx.lineWidth = 1;
        this.ctx.setLineDash([4, 4]);
        this.ctx.beginPath();
        this.ctx.moveTo(x, this.padding.top);
        this.ctx.lineTo(x, this.height - this.padding.bottom);
        this.ctx.stroke();
        this.ctx.setLineDash([]); // Reset dash

        // Draw circular node highlight
        this.ctx.fillStyle = '#ffffff';
        this.ctx.strokeStyle = this.options.primaryColor;
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(x, y, 4, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.stroke();

        // Draw hover tooltip box
        const text = `${item.date}: $${item.close.toFixed(2)}`;
        this.ctx.font = 'bold 9px Tahoma, sans-serif';
        const textWidth = this.ctx.measureText(text).width;
        
        let tooltipX = x + 10;
        let tooltipY = y - 15;
        
        // Keep tooltip bounds within plot layout
        if (tooltipX + textWidth + 12 > this.width) {
            tooltipX = x - textWidth - 22;
        }
        if (tooltipY < 10) {
            tooltipY = y + 10;
        }

        this.ctx.fillStyle = '#f7f9fc';
        this.ctx.strokeStyle = this.options.primaryColor;
        this.ctx.lineWidth = 1;
        this.ctx.fillRect(tooltipX, tooltipY, textWidth + 12, 18);
        this.ctx.strokeRect(tooltipX, tooltipY, textWidth + 12, 18);

        this.ctx.fillStyle = '#333333';
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(text, tooltipX + 6, tooltipY + 9);
    }

    drawDragSelection() {
        const xStart = this.getX(this.dragStartIndex);
        const xEnd = this.getX(this.dragEndIndex);
        const startPrice = this.data[this.dragStartIndex].close;
        const endPrice = this.data[this.dragEndIndex].close;
        const diff = endPrice - startPrice;
        const pct = (diff / startPrice) * 100;
        
        // Draw drag Selection box
        this.ctx.fillStyle = this.options.selectionColor;
        this.ctx.fillRect(xStart, this.padding.top, xEnd - xStart, this.plotHeight);

        // Left/Right selection border lines
        this.ctx.strokeStyle = this.options.primaryColor;
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.moveTo(xStart, this.padding.top);
        this.ctx.lineTo(xStart, this.height - this.padding.bottom);
        this.ctx.moveTo(xEnd, this.padding.top);
        this.ctx.lineTo(xEnd, this.height - this.padding.bottom);
        this.ctx.stroke();

        // Calculate mid X to center drag result details
        const midX = (xStart + xEnd) / 2;
        const direction = pct >= 0 ? '+' : '';
        const color = pct >= 0 ? '#006600' : '#cc0000';
        const text = `CHANGE MEASURE: ${direction}${pct.toFixed(2)}% (${direction}$${diff.toFixed(2)})`;
        
        this.ctx.font = 'bold 9px Tahoma, sans-serif';
        const textWidth = this.ctx.measureText(text).width;
        
        let tooltipX = midX - (textWidth + 12) / 2;
        // Boundary checks
        if (tooltipX < this.padding.left) tooltipX = this.padding.left + 5;
        if (tooltipX + textWidth + 12 > this.width - this.padding.right) {
            tooltipX = this.width - this.padding.right - textWidth - 17;
        }
        
        const tooltipY = this.padding.top + 10;
        
        this.ctx.fillStyle = pct >= 0 ? '#f3fbf3' : '#ffebe8'; // Light green vs light red
        this.ctx.strokeStyle = pct >= 0 ? '#008800' : '#dd3c10';
        this.ctx.lineWidth = 1;
        this.ctx.fillRect(tooltipX, tooltipY, textWidth + 12, 18);
        this.ctx.strokeRect(tooltipX, tooltipY, textWidth + 12, 18);

        this.ctx.fillStyle = color;
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(text, tooltipX + 6, tooltipY + 9);
    }

    render() {
        this.ctx.clearRect(0, 0, this.width, this.height);
        if (!this.data || this.data.length === 0) {
            this.ctx.fillStyle = '#888888';
            this.ctx.font = '11px Tahoma, sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.fillText("No historical quote data available.", this.width / 2, this.height / 2);
            return;
        }

        this.calculateScale();
        this.drawGridAndAxes();
        this.drawLine();
        
        // Render drag measurements overlay
        if (this.isDragging || (this.dragStartIndex !== -1 && this.dragEndIndex !== -1)) {
            this.drawDragSelection();
        }
        
        // Render simple hover price guide
        if (this.hoverIndex !== -1 && !this.isDragging) {
            this.drawHoverGuide();
        }
    }

    init() {
        this.setupCanvas();
        this.render();
        
        // Resize Handler
        window.addEventListener('resize', () => {
            this.setupCanvas();
            this.render();
        });

        // Mouse Position Resolvers
        const getMousePos = (e) => {
            const rect = this.canvas.getBoundingClientRect();
            return {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
        };

        const getNearestIndex = (x) => {
            if (x < this.padding.left) return 0;
            if (x > this.width - this.padding.right) return this.data.length - 1;
            const pct = (x - this.padding.left) / this.plotWidth;
            const idx = Math.round(pct * (this.data.length - 1));
            return Math.max(0, Math.min(this.data.length - 1, idx));
        };

        // Event Listeners
        this.canvas.addEventListener('mousemove', (e) => {
            const pos = getMousePos(e);
            const index = getNearestIndex(pos.x);
            
            if (this.isDragging) {
                this.dragEndIndex = index;
                this.dragCurrentX = pos.x;
            } else {
                this.hoverIndex = index;
            }
            this.render();
        });

        this.canvas.addEventListener('mousedown', (e) => {
            const pos = getMousePos(e);
            // Check bounding layout box
            if (pos.x >= this.padding.left && pos.x <= this.width - this.padding.right &&
                pos.y >= this.padding.top && pos.y <= this.height - this.padding.bottom) {
                
                // Clear any existing reset timeouts
                if (this.dragTimeout) {
                    clearTimeout(this.dragTimeout);
                    this.dragTimeout = null;
                }

                this.isDragging = true;
                this.dragStartX = pos.x;
                const idx = getNearestIndex(pos.x);
                this.dragStartIndex = idx;
                this.dragEndIndex = idx;
                this.render();
            }
        });

        const stopDragging = (e) => {
            if (this.isDragging) {
                this.isDragging = false;
                
                // Keep the measurement visible for 4 seconds so the user can easily read it
                this.dragTimeout = setTimeout(() => {
                    this.dragStartIndex = -1;
                    this.dragEndIndex = -1;
                    this.render();
                }, 4000);
            } else {
                this.hoverIndex = -1;
                this.render();
            }
        };

        this.canvas.addEventListener('mouseup', stopDragging);
        this.canvas.addEventListener('mouseleave', stopDragging);
    }
}
