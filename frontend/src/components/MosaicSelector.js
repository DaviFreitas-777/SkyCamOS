/**
 * SkyCamOS - Componente MosaicSelector
 * Seletor de layout de mosaico para cameras
 */

import { MOSAIC_LAYOUTS } from '../utils/constants.js';

class SkycamMosaicSelector extends HTMLElement {
    constructor() {
        super();
        this.currentLayout = '2x2';
    }

    static get observedAttributes() {
        return ['layout'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'layout' && oldValue !== newValue) {
            this.currentLayout = newValue;
            this.updateSelection();
        }
    }

    connectedCallback() {
        this.currentLayout = this.getAttribute('layout') || '2x2';
        this.render();
        this.attachEventListeners();
    }

    render() {
        const layouts = Object.keys(MOSAIC_LAYOUTS).filter(k => !MOSAIC_LAYOUTS[k].special);

        this.innerHTML = `
            <div class="mosaic-selector">
                ${layouts.map(layout => `
                    <button class="mosaic-option ${layout === this.currentLayout ? 'active' : ''}"
                            data-layout="${layout}" title="Layout ${layout}">
                        ${this.renderLayoutPreview(layout)}
                    </button>
                `).join('')}
            </div>
        `;

        this.addStyles();
    }

    renderLayoutPreview(layout) {
        const config = MOSAIC_LAYOUTS[layout];
        const cells = [];

        for (let i = 0; i < config.rows; i++) {
            for (let j = 0; j < config.cols; j++) {
                cells.push('<div class="mosaic-cell"></div>');
            }
        }

        return `
            <div class="mosaic-preview" style="grid-template-columns: repeat(${config.cols}, 1fr); grid-template-rows: repeat(${config.rows}, 1fr);">
                ${cells.join('')}
            </div>
        `;
    }

    addStyles() {
        if (document.getElementById('mosaic-selector-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'mosaic-selector-styles';
        styles.textContent = `
            .mosaic-selector { display: flex; gap: var(--spacing-xs); }
            .mosaic-option {
                width: 32px; height: 32px; padding: 4px;
                background: var(--color-bg-card); border: 1px solid var(--color-border-primary);
                border-radius: var(--radius-sm); cursor: pointer;
                transition: all var(--transition-fast);
            }
            .mosaic-option:hover { border-color: var(--color-primary-500); }
            .mosaic-option.active { border-color: var(--color-primary-500); background: var(--color-primary-900); }
            .mosaic-preview { display: grid; gap: 2px; width: 100%; height: 100%; }
            .mosaic-cell { background: var(--color-text-tertiary); border-radius: 1px; }
            .mosaic-option.active .mosaic-cell { background: var(--color-primary-400); }
        `;
        document.head.appendChild(styles);
    }

    attachEventListeners() {
        this.querySelectorAll('.mosaic-option').forEach(btn => {
            btn.addEventListener('click', () => {
                const layout = btn.dataset.layout;
                this.setLayout(layout);
            });
        });
    }

    setLayout(layout) {
        this.currentLayout = layout;
        this.updateSelection();
        this.dispatchEvent(new CustomEvent('layout-change', { detail: { layout }, bubbles: true }));
    }

    updateSelection() {
        this.querySelectorAll('.mosaic-option').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.layout === this.currentLayout);
        });
    }
}

customElements.define('skycam-mosaic-selector', SkycamMosaicSelector);
export default SkycamMosaicSelector;
