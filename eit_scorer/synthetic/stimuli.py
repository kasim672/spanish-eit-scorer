"""
eit_scorer/synthetic/stimuli.py
==================================
60 Spanish EIT stimulus sentences across CEFR levels A1–C2.
Used as the default corpus for synthetic dataset generation.
"""
from __future__ import annotations
from eit_scorer.data.models import EITItem

_STIMULI = [
    # ── A1 ───────────────────────────────────────────────────
    ("eit_01","El niño come una manzana roja.",4,"A1"),
    ("eit_02","La niña bebe agua fría.",4,"A1"),
    ("eit_03","El perro corre por el parque.",4,"A1"),
    ("eit_04","Ella tiene un libro azul.",4,"A1"),
    ("eit_05","Nosotros vivimos en una casa grande.",4,"A1"),
    ("eit_06","El gato duerme mucho.",4,"A1"),
    ("eit_07","María come pan con mantequilla.",4,"A1"),
    ("eit_08","Ellos juegan en el jardín.",4,"A1"),
    ("eit_09","Yo tengo dos hermanos.",4,"A1"),
    ("eit_10","El libro está en la mesa.",4,"A1"),
    # ── A2 ───────────────────────────────────────────────────
    ("eit_11","Nosotros vamos al mercado mañana.",4,"A2"),
    ("eit_12","La profesora habla con los estudiantes.",4,"A2"),
    ("eit_13","Ella necesita comprar leche y pan.",4,"A2"),
    ("eit_14","Los perros corren rápidamente por el parque.",4,"A2"),
    ("eit_15","Mi madre cocina muy bien todos los días.",4,"A2"),
    ("eit_16","El estudiante lee el libro con interés.",4,"A2"),
    ("eit_17","Sus padres vinieron desde muy lejos.",4,"A2"),
    ("eit_18","Siempre llega tarde a sus clases.",4,"A2"),
    ("eit_19","El médico trabaja en el hospital grande.",4,"A2"),
    ("eit_20","La familia come junta en la noche.",4,"A2"),
    # ── B1 ───────────────────────────────────────────────────
    ("eit_21","María le dio el regalo a su madre.",4,"B1"),
    ("eit_22","El médico le recetó medicamentos al paciente.",4,"B1"),
    ("eit_23","Las flores del jardín son muy bonitas.",4,"B1"),
    ("eit_24","Tenemos que estudiar mucho para el examen.",4,"B1"),
    ("eit_25","El perro grande persiguió al gato pequeño.",4,"B1"),
    ("eit_26","Sus padres vinieron desde muy lejos para verla.",4,"B1"),
    ("eit_27","El estudiante leyó el libro con mucho interés.",4,"B1"),
    ("eit_28","La semana pasada fuimos al cine con los amigos.",4,"B1"),
    ("eit_29","Mi hermano aprendió a cocinar durante la pandemia.",4,"B1"),
    ("eit_30","Ella se despertó temprano para ir al trabajo.",4,"B1"),
    # ── B2 ───────────────────────────────────────────────────
    ("eit_31","Quiero que vengas a la fiesta esta noche.",4,"B2"),
    ("eit_32","Es importante que los estudiantes practiquen todos los días.",4,"B2"),
    ("eit_33","Me alegra que hayas llegado a tiempo.",4,"B2"),
    ("eit_34","Le pedí que me explicara el problema con más detalle.",4,"B2"),
    ("eit_35","Aunque estaba cansada, terminó todo el trabajo.",4,"B2"),
    ("eit_36","El informe que presentó el director fue muy completo.",4,"B2"),
    ("eit_37","Se lo explicaré cuando tenga más tiempo.",4,"B2"),
    ("eit_38","Los resultados del estudio nos sorprendieron mucho.",4,"B2"),
    ("eit_39","Había mucha gente cuando llegamos al aeropuerto.",4,"B2"),
    ("eit_40","La empresa se ha visto obligada a cerrar varios departamentos.",4,"B2"),
    # ── C1 ───────────────────────────────────────────────────
    ("eit_41","Si hubieras llegado antes, habrías visto la presentación.",4,"C1"),
    ("eit_42","Es fundamental que se revisen los protocolos de seguridad.",4,"C1"),
    ("eit_43","A pesar de los esfuerzos realizados, no se lograron los objetivos.",4,"C1"),
    ("eit_44","La hipótesis que se planteó inicialmente resultó ser incorrecta.",4,"C1"),
    ("eit_45","Me sorprende que no hayan considerado esa alternativa.",4,"C1"),
    ("eit_46","Las consecuencias de esa decisión se harán evidentes con el tiempo.",4,"C1"),
    ("eit_47","Habría sido mejor consultar a los expertos antes de actuar.",4,"C1"),
    ("eit_48","El análisis estadístico demostró que los resultados eran significativos.",4,"C1"),
    ("eit_49","Se desconoce si el fenómeno obedece a causas naturales o artificiales.",4,"C1"),
    ("eit_50","La propuesta fue rechazada por no cumplir con los criterios establecidos.",4,"C1"),
    # ── C2 ───────────────────────────────────────────────────
    ("eit_51","Cabe preguntarse si las medidas adoptadas surtirán el efecto deseado.",4,"C2"),
    ("eit_52","El fenómeno fue objeto de debate durante décadas sin llegar a conclusión.",4,"C2"),
    ("eit_53","Se arguyó que los datos presentados carecían de validez empírica.",4,"C2"),
    ("eit_54","La ambigüedad inherente al texto dificultó su interpretación unívoca.",4,"C2"),
    ("eit_55","Habida cuenta de los antecedentes, la resolución resultó previsible.",4,"C2"),
    ("eit_56","Los paradigmas teóricos vigentes resultan insuficientes para explicarlo.",4,"C2"),
    ("eit_57","El fallo judicial fue recurrido por considerarse desproporcionado.",4,"C2"),
    ("eit_58","La dicotomía entre forma y contenido subyace a toda producción artística.",4,"C2"),
    ("eit_59","La reconfiguración del espacio urbano conlleva implicaciones sociales profundas.",4,"C2"),
    ("eit_60","El esclarecimiento de los hechos depende de que se aporten nuevas pruebas.",4,"C2"),
]


def default_stimuli_60() -> list[EITItem]:
    """Return the 60 default EIT stimulus sentences as EITItem objects."""
    return [
        EITItem(item_id=sid, reference=ref, max_points=mp, level=lvl)
        for sid, ref, mp, lvl in _STIMULI
    ]
