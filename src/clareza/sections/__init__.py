# coding: utf-8
"""Sections package for Clareza reflection reports."""

from clareza.sections.diagnostico import generate_diagnostico
from clareza.sections.interpretacao import generate_interpretacao
from clareza.sections.riscos import generate_riscos
from clareza.sections.decisoes import generate_decisoes
from clareza.sections.plano import generate_plano

__all__ = [
    "generate_diagnostico",
    "generate_interpretacao",
    "generate_riscos",
    "generate_decisoes",
    "generate_plano",
]