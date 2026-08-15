from dataclasses import dataclass
from typing import Tuple

from .anotacion_nlp import AnotacionNLP
from .clasificacion_fragmento import FragmentoClasificado
from .texto_normalizado import TextoNormalizado


@dataclass(frozen=True)
class ResultadoAnalisisNLP:
    texto_normalizado: TextoNormalizado
    fragmentos_clasificados: Tuple[FragmentoClasificado, ...]
    anotaciones: Tuple[AnotacionNLP, ...]
