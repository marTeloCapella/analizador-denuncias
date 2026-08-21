import streamlit as st
import json
from google import genai
from google.genai import types
from pypdf import PdfReader

st.set_page_config(page_title="Analizador Judicial Pro", page_icon="⚖️", layout="wide")

# PANEL IZQUIERDO DE CONFIGURACIÓN Y SELECCIÓN DE MATERIA
with st.sidebar:
    st.header("🔑 Seguridad y Módulo")
    api_key_usuario = st.text_input("Pegá tu Google API Key acá:", type="password")
    st.markdown("[👉 Conseguí tu clave gratis en un minuto](https://google.com)")
    st.markdown("---")
    
    # El botón selector que cambia el comportamiento de la IA según el caso
    modulo_seleccionado = st.radio(
        "Seleccioná la materia a analizar:",
        ["🚨 Violencia Familiar (Ley 12.569)", "🌾 Juicio de Alimentos"],
        index=0
    )
    st.caption("🔒 Privacidad garantizada: Los datos viajan encriptados de forma directa a Google. No se guardan copias de escritos ni PDFs.")

# TÍTULOS DINÁMICOS SEGÚN EL MÓDULO SELECCIONADO
if modulo_seleccionado == "🚨 Violencia Familiar (Ley 12.569)":
    st.title("⚖️ Analizador de Denuncias Familiares")
    st.caption("Módulo de Violencia - Extractor automático de denuncias policiales y factores de riesgo.")
else:
    st.title("⚖️ Analizador de Demandas de Alimentos")
    st.caption("Módulo de Alimentos - Extractor de datos filiatorios, gastos, baches de ingresos y alertas de rito.")

archivo_pdf = st.file_uploader("Subí acá el escrito o expediente en formato PDF:", type=["pdf"])

if archivo_pdf is not None:
    st.info("Archivo cargado correctamente. Procesando páginas...")
    
    if st.button("Analizar y Extraer Datos"):
        if not api_key_usuario:
            st.error("⚠️ Falta la configuración de seguridad. Por favor, ingresá tu Google API Key en el panel de la izquierda.")
        else:
            with st.spinner("Leyendo el documento y clasificando la información en base al criterio del Juzgado..."):
                try:
                    lector_pdf = PdfReader(archivo_pdf)
                    texto_completo = ""
                    for pagina in lector_pdf.pages:
                        texto_extraido = pagina.extract_text()
                        if texto_extraido:
                            texto_completo += texto_extraido + "\n"
                    
                    if not texto_completo.strip():
                        st.error("No se pudo extraer texto. Asegurate de que no sea una imagen escaneada borrosa.")
                    else:
                        client = genai.Client(api_key=api_key_usuario)
                        
                        # CONFIGURACIÓN DE PROMPTS SEGÚN LA MATERIA
                        if modulo_seleccionado == "🚨 Violencia Familiar (Ley 12.569)":
                            prompt_sistema = """
                            Actuás como un prosecretario de un Juzgado de Familia de la Pba, experto en violencia familiar.
                            Analizá el texto y respondé UNICAMENTE con un objeto JSON válido con estas llaves:
                            {
                              "resumen_hechos": "Resumen ejecutivo muy breve de los hechos denunciados (máximo 4 líneas).",
                              "denunciantes_detallados": [{"nombre": "Nombre", "dni": "DNI", "domicilio": "Domicilio", "telefono": "Teléfono", "email": "Email", "vinculo": "Vínculo"}],
                              "denunciados_detallados": [{"nombre": "Nombre", "dni": "DNI", "domicilio": "Domicilio", "telefono": "Teléfono", "email": "Email"}],
                              "menores_involucrados": ["Nombre, edad, situación."],
                              "antecedentes_penales": "Mención sobre causas penales del denunciado. Si no hay, 'No surgen'.",
                              "antecedentes_entre_ellos": "Mención sobre denuncias previas entre las partes. Si no hay, 'No surgen'.",
                              "comisaria_interviniente": "Comisaría que tomó la denuncia.",
                              "comisaria_por_jurisdiccion": "Deducción de la comisaría de seguridad que corresponde al domicilio del denunciante en PBA.",
                              "medidas_solicitadas": ["Medidas solicitadas."],
                              "indicadores_riesgo": ["Factores de riesgo detectados."]
                            }
                            """
                        else:
                            # PROMPT COMPLETO DE ALIMENTOS EN BASE A TUS NUEVOS REQUISITOS
                            prompt_sistema = """
                            Actuás como un prosecretario de un Juzgado de Familia de la Pba, experto en juicios de alimentos.
                            Analizá el escrito de demanda provisto y extraé la información procesal relevante de forma estructurada.
                            Debes responder UNICAMENTE con un objeto JSON válido que contenga las siguientes llaves:
                            {
                              "actor_detallado": {"nombre": "Nombre completo", "dni": "DNI", "domicilio_real": "Domicilio real denunciado", "domicilio_electronico": "Domicilio electrónico del letrado"},
                              "demandado_detallado": {"nombre": "Nombre completo", "dni": "DNI/CUIL si figuran", "domicilio_real": "Domicilio real denunciado"},
                              "menores_filiatorios": ["Lista con Nombre completo, DNI y edad de cada hijo menor de edad por el que se reclama."],
                              "ingresos_denunciados": "Detalle de los ingresos declarados u ofrecidos por la parte actora, y estimación/denuncia sobre el trabajo, ingresos o nivel de vida del demandado (ej: si trabaja en negro, en qué empresa, etc.).",
                              "regimen_vida_menores": "Resumen breve de cómo es el régimen de vida y cuidado de los menores (ej: si el cuidado es exclusivo de la madre, si se denunció incumplimiento del régimen de comunicación, etc.).",
                              "liquidacion_gastos_detalle": "Detalle pormenorizado de la liquidación de gastos mensuales acompañada (ej: monto total estimativo, gastos de colegio, obra social, esparcimiento, alquiler). Si no acompaña cuadro de gastos, poner 'No se adjunta detalle'.",
                              "cuestion_especial_menor": "Mención explícita sobre si algún menor padece una enfermedad, tratamiento o si cuenta con Certificado Único de Discapacidad (CUD). Si no menciona nada, poner 'No surgen del texto'.",
                              "franja_18_25_estudiantes": "Identificación de si alguno de los hijos se encuentra en la franja de 18 a 25 años y si la demanda acredita o menciona su condición de estudiante/formación para mantener el derecho alimentario. Si no hay hijos en esa edad, poner 'No aplica'.",
                              "prueba_ofrecida": {"documental_instrumental": "Detalle corto", "testimonial": "Detalle corto", "confesional_pericial_informativa": "Detalle corto"},
                              "expedientes_conexos": "Mención de otros expedientes en trámite entre las partes (ej: violencia familiar, pautas de cuidado, divorcio, etc.). Si no hay, poner 'No se denuncian'."
                            }
                            No agregues introducciones ni textos fuera del JSON.
                            """

                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=f"{prompt_sistema}\n\nTexto del documento:\n{texto_completo}",
                            config=types.GenerateContentConfig(response_mime_type="application/json")
                        )
                        
                        resultado = json.loads(response.text)
                        st.success("¡Análisis completado con éxito!")
                        
                        # RENDERIZADO VISUAL DINÁMICO SEGÚN LA MATERIA
                        if modulo_seleccionado == "🚨 Violencia Familiar (Ley 12.569)":
                            col1, col2 = st.columns(2)
                            with col1:
                                st.subheader("📝 Resumen de Hechos")
                                st.write(resultado.get("resumen_hechos"))
                                st.subheader("👥 Datos de las Partes")
                                st.markdown("**🚨 DENUNCIANTE(S):**")
                                for d in resultado.get("denunciantes_detallados", []):
                                    st.write(f"- {d.get('nombre')} (DNI: {d.get('dni')}) | Dom: {d.get('domicilio')} | Tel: {d.get('telefono')}")
                                st.markdown("**👤 DENUNCIADO(S):**")
                                for d in resultado.get("denunciados_detallados", []):
                                    st.write(f"- {d.get('nombre')} (DNI: {d.get('dni')}) | Dom: {d.get('domicilio')}")
                                st.subheader("📂 Historial y Antecedentes")
                                st.markdown(f"**Entre las partes:** {resultado.get('antecedentes_entre_ellos')}")
                                st.markdown(f"**Penales:** {resultado.get('antecedentes_penales')}")
                            with col2:
                                st.subheader("👶 Menores Involucrados")
                                for m in resultado.get("menores_involucrados", []): st.write(f"- {m}")
                                st.subheader("👮 Información Policial")
                                st.write(f"- **Intervino:** {resultado.get('comisaria_interviniente')}")
                                st.write(f"- **Jurisdicción por Domicilio:** {resultado.get('comisaria_por_jurisdiccion')}")
                                st.subheader("🛑 Cautelares y Riesgo")
                                st.markdown("**Solicitadas:**")
                                for med in resultado.get("medidas_solicitadas", []): st.write(f"- {med}")
                                st.markdown("**Indicadores de Riesgo:**")
