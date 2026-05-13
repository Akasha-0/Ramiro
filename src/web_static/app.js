/** Interface web — Clareza
 *
 * Módulo JavaScript para interação com a API de análise.
 * Gerencia form submission, requisições HTTP e renderização de resultados.
 */

(function() {
    'use strict';

    // ------------------------------------------------------------------
    // Estado
    // ------------------------------------------------------------------

    const state = {
        isLoading: false,
        history: [],
    };

    // ------------------------------------------------------------------
    // Elementos do DOM
    // ------------------------------------------------------------------

    const elements = {
        get inputText() { return document.getElementById('content'); },
        get formatSelect() { return document.getElementById('formatSelect'); },
        get analyzeBtn() { return document.getElementById('analyzeBtn'); },
        get resultSection() { return document.getElementById('resultSection'); },
        get reportOutput() { return document.getElementById('reportOutput'); },
        get historySection() { return document.getElementById('historySection'); },
        get historyList() { return document.getElementById('historyList'); },
        get refreshHistoryBtn() { return document.getElementById('refreshHistoryBtn'); },
        get clearHistoryBtn() { return document.getElementById('clearHistoryBtn'); },
    };

    // ------------------------------------------------------------------
    // Utilitários
    // ------------------------------------------------------------------

    /**
     * Obtem os valores atuais do formulário.
     * @returns {Object} Objeto com input e format.
     */
    function getFormData() {
        return {
            input: elements.inputText.value.trim(),
            format: elements.formatSelect.value,
        };
    }

    /**
     * Habilita ou desabilita o formulário durante requisições.
     * @param {boolean} disabled - Se true, desabilita o formulário.
     */
    function setFormDisabled(disabled) {
        elements.inputText.disabled = disabled;
        elements.formatSelect.disabled = disabled;
        elements.analyzeBtn.disabled = disabled;
        state.isLoading = disabled;
    }

    /**
     * Exibe mensagem de erro no resultado.
     * @param {string} message - Mensagem de erro.
     * @param {string} [details] - Detalhes adicionais.
     */
    function showError(message, details) {
        elements.resultSection.hidden = false;
        elements.reportOutput.className = 'report-content error';
        let text = 'Erro: ' + message;
        if (details) {
            text += '\n\nDetalhes: ' + details;
        }
        elements.reportOutput.textContent = text;
    }

    /**
     * Exibe o relatório no resultado.
     * @param {string} report - Conteúdo do relatório em Markdown.
     */
    function showReport(report) {
        elements.resultSection.hidden = false;
        elements.reportOutput.className = 'report-content success';
        elements.reportOutput.textContent = report;
    }

    /**
     * Formata timestamp para exibição legível.
     * @param {number} timestamp - Timestamp Unix.
     * @returns {string} Data formatada.
     */
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp * 1000);
        return date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    }

    /**
     * Salva entrada no histórico do servidor.
     * @param {Object} data - Dados da entrada.
     * @returns {Promise<Object>} Promessa com a entrada salva.
     */
    async function saveToHistory(data) {
        const response = await fetch('/api/history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Erro desconhecido');
        }

        return result.entry;
    }

    /**
     * Carrega histórico do servidor.
     * @returns {Promise<Array>} Lista de entradas do histórico.
     */
    async function loadHistory() {
        const response = await fetch('/api/history');

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Erro desconhecido');
        }

        return data.history;
    }

    /**
     * Renderiza um item de histórico na lista.
     * @param {Object} entry - Entrada do histórico.
     * @returns {HTMLElement} Elemento do item.
     */
    function renderHistoryItem(entry) {
        const item = document.createElement('div');
        item.className = 'history-item';
        item.dataset.id = entry.id;

        const header = document.createElement('div');
        header.className = 'history-item-header';

        const inputText = document.createElement('span');
        inputText.className = 'history-item-input';
        inputText.textContent = entry.input;

        const meta = document.createElement('span');
        meta.className = 'history-item-meta';
        meta.innerHTML = '<span>' + entry.format + '</span><span>' + formatTimestamp(entry.timestamp) + '</span>';

        header.appendChild(inputText);
        header.appendChild(meta);

        const preview = document.createElement('div');
        preview.className = 'history-item-preview';
        preview.textContent = entry.report.substring(0, 100) + (entry.report.length > 100 ? '...' : '');

        const detail = document.createElement('div');
        detail.className = 'history-item-detail';
        detail.textContent = entry.report;

        item.appendChild(header);
        item.appendChild(preview);
        item.appendChild(detail);

        item.addEventListener('click', function() {
            detail.classList.toggle('visible');
        });

        return item;
    }

    /**
     * Renderiza a lista de histórico.
     */
    function renderHistory() {
        elements.historyList.innerHTML = '';

        if (state.history.length === 0) {
            elements.historyList.innerHTML = '<div class="history-empty">Nenhum histórico disponível</div>';
            return;
        }

        state.history.forEach(function(entry) {
            elements.historyList.appendChild(renderHistoryItem(entry));
        });
    }

    /**
     * Carrega e exibe o histórico.
     */
    async function refreshHistory() {
        try {
            state.history = await loadHistory();
            renderHistory();
        } catch (err) {
            console.error('Erro ao carregar histórico:', err.message);
        }
    }

    /**
     * Salva análise atual no histórico.
     * @param {string} input - Entrada.
     * @param {string} format - Formato.
     * @param {string} report - Relatório.
     */
    async function addToHistory(input, format, report) {
        try {
            await saveToHistory({ input: input, format: format, report: report });
            await refreshHistory();
        } catch (err) {
            console.error('Erro ao salvar no histórico:', err.message);
        }
    }

    // ------------------------------------------------------------------
    // API
    // ------------------------------------------------------------------

    /**
     * Envia requisição de análise para o servidor.
     * @param {string} input - Texto ou símbolos de entrada.
     * @param {string} format - Formato da entrada.
     * @returns {Promise<string>} Promessa com o relatório.
     */
    async function analyze(input, format) {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ input: input, format: format }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Erro desconhecido');
        }

        return data.report;
    }

    // ------------------------------------------------------------------
    // Event handlers
    // ------------------------------------------------------------------

    /**
     * Manipula submit do formulário de análise.
     * @param {Event} event - Evento de submit.
     */
    async function handleAnalyze(event) {
        event.preventDefault();

        const formData = getFormData();

        if (!formData.input) {
            showError('Campo de entrada vazio', 'Por favor, preencha o campo de texto.');
            return;
        }

        setFormDisabled(true);
        showError('', '');

        try {
            const report = await analyze(formData.input, formData.format);
            showReport(report);
            addToHistory(formData.input, formData.format, report);
        } catch (err) {
            showError('Falha na análise', err.message);
        } finally {
            setFormDisabled(false);
        }
    }

    // ------------------------------------------------------------------
    // Inicialização
    // ------------------------------------------------------------------

    /**
     * Inicializa a interface web.
     */
    function init() {
        elements.analyzeBtn.addEventListener('click', handleAnalyze);

        elements.inputText.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && event.ctrlKey) {
                handleAnalyze(event);
            }
        });

        elements.refreshHistoryBtn.addEventListener('click', refreshHistory);

        elements.clearHistoryBtn.addEventListener('click', function() {
            state.history = [];
            renderHistory();
        });

        refreshHistory();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
