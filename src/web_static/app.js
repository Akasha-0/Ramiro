/** Interface web — Clareza
 *
 * Módulo JavaScript para interação com a API de análise.
 * Gerencia form submission, requisições fetch e renderização de resultados.
 */

(function() {
    'use strict';

    // ------------------------------------------------------------------
    // Estado
    // ------------------------------------------------------------------

    const state = {
        isLoading: false,
    };

    // ------------------------------------------------------------------
    // Elementos do DOM
    // ------------------------------------------------------------------

    const elements = {
        get inputText() { return document.getElementById('inputText'); },
        get formatSelect() { return document.getElementById('formatSelect'); },
        get analyzeBtn() { return document.getElementById('analyzeBtn'); },
        get resultSection() { return document.getElementById('resultSection'); },
        get reportOutput() { return document.getElementById('reportOutput'); },
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
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
