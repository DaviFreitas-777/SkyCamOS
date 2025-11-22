/**
 * SkyCamOS - Componente Timeline
 * Timeline para navegacao em gravacoes
 */

import { formatTime, formatDate } from '../utils/dateFormatter.js';

class SkycamTimeline extends HTMLElement {
    constructor() {
        super();
        this.startTime = null;
        this.endTime = null;
        this.currentTime = null;
        this.segments = [];
        this.isDragging = false;
    }

    static get observedAttributes() {
        return ['start-time', 'end-time', 'current-time'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue === newValue) return;
        switch (name) {
            case 'start-time': this.startTime = new Date(newValue); break;
            case 'end-time': this.endTime = new Date(newValue); break;
            case 'current-time': this.currentTime = new Date(newValue); break;
        }
        if (this.isConnected) this.render();
    }

    connectedCallback() {
        this.render();
        this.attachEventListeners();
    }

    render() {
        const cursorPosition = this.getCursorPosition();

        this.innerHTML = `
            <div class="timeline">
                <div class="timeline-header">
                    <span class="timeline-date">${this.startTime ? formatDate(this.startTime) : 'Hoje'}</span>
                    <div class="timeline-time-display">
                        <span id="current-time-display">${this.currentTime ? formatTime(this.currentTime, true) : '00:00:00'}</span>
                    </div>
                </div>
                <div class="timeline-track" id="timeline-track">
                    <div class="timeline-segments" id="timeline-segments"></div>
                    <div class="timeline-cursor" id="timeline-cursor" style="left: ${cursorPosition}%">
                        <div class="timeline-cursor-handle"></div>
                    </div>
                </div>
                <div class="timeline-scale">
                    ${this.renderTimeScale()}
                </div>
                <div class="timeline-controls">
                    <button class="btn btn-icon-sm btn-ghost" id="timeline-prev">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="19" x2="5" y2="5"/>
                        </svg>
                    </button>
                    <button class="btn btn-icon-sm btn-ghost" id="timeline-play">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <polygon points="5 3 19 12 5 21 5 3"/>
                        </svg>
                    </button>
                    <button class="btn btn-icon-sm btn-ghost" id="timeline-next">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/>
                        </svg>
                    </button>
                    <select class="input timeline-speed" id="playback-speed">
                        <option value="0.5">0.5x</option>
                        <option value="1" selected>1x</option>
                        <option value="2">2x</option>
                        <option value="4">4x</option>
                    </select>
                </div>
            </div>
        `;
        this.addStyles();
        this.renderSegments();
    }

    renderTimeScale() {
        const hours = [];
        for (let i = 0; i <= 24; i += 4) {
            hours.push(`<span class="timeline-hour" style="left: ${(i / 24) * 100}%">${String(i).padStart(2, '0')}:00</span>`);
        }
        return hours.join('');
    }

    renderSegments() {
        const container = this.querySelector('#timeline-segments');
        if (!container) return;
        container.innerHTML = this.segments.map(seg => {
            const left = this.timeToPercent(seg.start);
            const width = this.timeToPercent(seg.end) - left;
            return `<div class="timeline-segment ${seg.type}" style="left: ${left}%; width: ${width}%"></div>`;
        }).join('');
    }

    getCursorPosition() {
        if (!this.currentTime || !this.startTime || !this.endTime) return 0;
        const total = this.endTime.getTime() - this.startTime.getTime();
        const current = this.currentTime.getTime() - this.startTime.getTime();
        return Math.max(0, Math.min(100, (current / total) * 100));
    }

    timeToPercent(time) {
        if (!this.startTime || !this.endTime) return 0;
        const date = new Date(time);
        const total = this.endTime.getTime() - this.startTime.getTime();
        const pos = date.getTime() - this.startTime.getTime();
        return Math.max(0, Math.min(100, (pos / total) * 100));
    }

    percentToTime(percent) {
        if (!this.startTime || !this.endTime) return null;
        const total = this.endTime.getTime() - this.startTime.getTime();
        return new Date(this.startTime.getTime() + (total * percent / 100));
    }

    addStyles() {
        if (document.getElementById('timeline-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'timeline-styles';
        styles.textContent = `
            .timeline { background: var(--color-bg-card); border-radius: var(--radius-lg); padding: var(--spacing-md); }
            .timeline-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-sm); }
            .timeline-date { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
            .timeline-time-display { font-family: var(--font-family-mono); font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); }
            .timeline-track { position: relative; height: 40px; background: var(--color-bg-tertiary); border-radius: var(--radius-md); cursor: pointer; margin: var(--spacing-sm) 0; }
            .timeline-segments { position: absolute; inset: 0; overflow: hidden; border-radius: var(--radius-md); }
            .timeline-segment { position: absolute; top: 0; height: 100%; background: var(--color-primary-600); opacity: 0.8; }
            .timeline-segment.motion { background: var(--color-warning); }
            .timeline-segment.event { background: var(--color-error); }
            .timeline-cursor { position: absolute; top: -4px; bottom: -4px; width: 2px; background: var(--color-error); z-index: 10; transform: translateX(-50%); }
            .timeline-cursor-handle { position: absolute; top: -6px; left: -5px; width: 12px; height: 12px; background: var(--color-error); border-radius: 50%; cursor: grab; }
            .timeline-scale { position: relative; height: 20px; font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
            .timeline-hour { position: absolute; transform: translateX(-50%); }
            .timeline-controls { display: flex; align-items: center; justify-content: center; gap: var(--spacing-sm); margin-top: var(--spacing-sm); }
            .timeline-speed { width: 70px; padding: var(--spacing-xs); font-size: var(--font-size-xs); }
        `;
        document.head.appendChild(styles);
    }

    attachEventListeners() {
        const track = this.querySelector('#timeline-track');
        const cursor = this.querySelector('#timeline-cursor');

        track?.addEventListener('click', (e) => {
            const rect = track.getBoundingClientRect();
            const percent = ((e.clientX - rect.left) / rect.width) * 100;
            this.seekTo(percent);
        });

        cursor?.addEventListener('mousedown', () => { this.isDragging = true; });
        document.addEventListener('mousemove', (e) => {
            if (!this.isDragging) return;
            const rect = track.getBoundingClientRect();
            const percent = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100));
            cursor.style.left = `${percent}%`;
        });
        document.addEventListener('mouseup', () => {
            if (this.isDragging) {
                const percent = parseFloat(cursor?.style.left || '0');
                this.seekTo(percent);
            }
            this.isDragging = false;
        });

        this.querySelector('#timeline-play')?.addEventListener('click', () => this.togglePlay());
        this.querySelector('#timeline-prev')?.addEventListener('click', () => this.skipBack());
        this.querySelector('#timeline-next')?.addEventListener('click', () => this.skipForward());
    }

    seekTo(percent) {
        const time = this.percentToTime(percent);
        if (time) {
            this.dispatchEvent(new CustomEvent('timeline-seek', { detail: { time }, bubbles: true }));
        }
    }

    togglePlay() {
        this.dispatchEvent(new CustomEvent('timeline-play', { bubbles: true }));
    }

    skipBack() {
        this.dispatchEvent(new CustomEvent('timeline-skip', { detail: { direction: -1, seconds: 10 }, bubbles: true }));
    }

    skipForward() {
        this.dispatchEvent(new CustomEvent('timeline-skip', { detail: { direction: 1, seconds: 10 }, bubbles: true }));
    }

    setSegments(segments) {
        this.segments = segments;
        this.renderSegments();
    }

    updateCursor(time) {
        this.currentTime = new Date(time);
        const cursor = this.querySelector('#timeline-cursor');
        const display = this.querySelector('#current-time-display');
        if (cursor) cursor.style.left = `${this.getCursorPosition()}%`;
        if (display) display.textContent = formatTime(this.currentTime, true);
    }
}

customElements.define('skycam-timeline', SkycamTimeline);
export default SkycamTimeline;
