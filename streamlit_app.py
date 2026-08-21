import streamlit as st
import json
from google import genai
from google.genai import types
from pypdf import PdfReader

st.set_page_config(page_title="Analizador de Denuncias", page_icon="⚖️", layout="wide")

with st.sidebar:
    st.header("🔑 Configuración de Seguridad")
    st.markdown("Para usar este analizador gratuito, ingresá tu clave API de Google Gemini.")
    api_key_usuario = st.text_input("Pegá tu Google API Key acá:", type="password")
    st.markdown("[👉 Conseguí tu clave gratis en un minuto haciendo clic acá](https://google.com)")
    st.caption("🔒 Privacidad garantizada: Tu clave y los datos del expediente viajan encriptados de forma directa a Google. Este sitio no almacena registros, nombres ni documentos.")

st.title("⚖️ Analizador de Denuncias Familiares")
st.caption("Herramienta de optimización interna para Juzgados de Familia. Extractor automático de datos desde PDF.")

archivo_pdf = st.file_uploader("Subí acá el expediente o denuncia en formato PDF:", type=["pdf"])

if archivo_pdf is not None:
    st.info("Archivo cargado correctamente. Procesando páginas...")
    
    if st.button("Analizar y Extraer Datos"):
        if not api_key_usuario:
            st.error("⚠️ Falta la configuración de seguridad. Por favor, ingresá tu Google API Key en el panel de la izquierda para poder procesar el archivo.")
        else:
            with st.spinner("Leyendo el PDF y clasificando la información del expediente..."):
                try:
                    lector_pdf = PdfReader(archivo_pdf)
                    texto_completo = ""
                    for pagina in lector_pdf.pages:
                        texto_extraido = pagina.extract_text()
                        if texto_extraido:
                            texto_completo += texto_extraido + "\n"
                    
                    if not texto_completo.strip():
                        st.error("No se pudo extraer texto de este PDF. Asegurate de que no sea una imagen escaneada borrosa o un formato no compatible.")
                    else:
                        client = genai.Client(api_key=api_key_usuario)
                        
                        prompt_sistema = """
                        Actuás como un prosecretario de un Juzgado de Familia de la Provincia de Buenos Aires, experto en el análisis preliminar de denuncias por violencia familiar (Ley 12.569).
                        Tu tarea es analizar el texto de la denuncia provisto y extraer la información estrictamente necesaria de forma estructurada.
                        
                        Debes responder UNICAMENTE con un objeto JSON válido que contenga las siguientes llaves:
                        {
                          "resumen_hechos": "Un resumen ejecutivo muy breve, claro y cronológico de los hechos denunciados (máximo 4 líneas).",
                          "denunciantes_detallados": [
                             {"nombre": "Nombre completo", "dni": "DNI", "domicilio": "Domicilio real", "telefono": "Teléfono", "email": "Email", "vinculo": "Vínculo con denunciado"}
                          ],
                          "denunciados_detallados": [
                             {"nombre": "Nombre completo", "dni": "DNI", "domicilio": "Domicilio real", "telefono": "Teléfono", "email": "Email"}
                          ],
                          "menores_involucrados": ["Nombre, edad, situación. Indicar 'Ninguno' si no hay"],
                          "antecedentes_penales": "Mención explícita en el texto sobre antecedentes penales o causas penales del denunciado (ej: IPP en trámite). Si no figura, poner 'No surgen del texto'.",
                          "antecedentes_entre_ellos": "Mención en el texto sobre denuncias previas o violencia anterior entre las partes. Si no figura, poner 'No surgen del texto'.",
                          "comisaria_interviniente": "Nombre de la comisaría o destacamento que tomó la denuncia (ej: Comisaría de la Mujer y la Familia de San Isidro).",
                          "comisaria_por_jurisdiccion": "Deducción razonable de qué comisaría de seguridad de la zona (ej: San Isidro 1ra, Martínez 2da, Tigre 1ra, etc.) corresponde al domicilio real de la persona denunciante según el partido de la Provincia de Buenos Aires en el que vive.",
                          "medidas_solicitadas": ["Lista de las medidas que pide el denunciante o sugiere la policía."],
                          "indicadores_riesgo": ["Factores de riesgo: presencia de armas, drogas, amenazas de muerte, perimetrales violadas."]
                        }
                        No agregues introducciones ni textos fuera del JSON.
                        """
                        
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=f"{prompt_sistema}\n\nTexto de la denuncia:\n{texto_completo}",
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json"
                            )
                        )
                        
                        resultado = json.loads(response.text)
                        st.success("¡Análisis completado con éxito!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("📝 Resumen de Hechos")
                            st.write(resultado.get("resumen_hechos"))
                            
                            st.subheader("👥 Datos de las Partes")
                            st.markdown("**🚨 DENUNCIANTE(S):**")
                            for d in resultado.get("denunciantes_detallados", []):
                                st.write(f"- **Nombre:** {d.get('nombre')}")
                                st.write(f"  - **DNI:** {d.get('dni')} | **Vínculo:** {d.get('vinculo')}")
                                st.write(f"  - **Domicilio:** {d.get('domicilio')}")
                                st.write(f"  - **Teléfono:** {d.get('telefono')} | **Email:** {d.get('email')}")
                            
                            st.markdown("---")
                            st.markdown("**👤 DENUNCIADO(S):**")
                            for d in resultado.get("denunciados_detallados", []):
                                st.write(f"- **Nombre:** {d.get('nombre')}")
                                st.write(f"  - **DNI:** {d.get('dni')}")
                                st.write(f"  - **Domicilio:** {d.get('domicilio')}")
                                i_tel = d.get('telefono')
                                i_mail = d.get('email')
                                st.write(f"  - **Teléfono:** {i_tel if i_tel else 'No figura'} | **Email:** {i_mail if i_mail else 'No figura'}")

                            st.subheader("📂 Historial y Antecedentes")
                            st.markdown("**Entre las partes:**")
                            st.write(resultado.get("antecedentes_entre_ellos"))
                            st.markdown("**Causas penales / Otros antecedentes:**")
                            st.write(resultado.get("antecedentes_penales"))
                            
                        with col2:
                            st.subheader("👶 Menores Involucrados")
                            for m in resultado.get("menores_involucrados", []): st.write(f"- {m}")
                            
                            st.subheader("👮 Información Policial")
                            st.markdown(f"**Comisaría que intervino:** {resultado.get('comisaria_interviniente')}")
                            st.markdown(f"**Comisaría correspondiente por domicilio:** {resultado.get('comisaria_por_jurisdiccion')}")
                            
                            st.subheader("🛑 Medidas Cautelares Solicitadas")
                            for med in resultado.get("medidas_solicitadas", []): st.write(f"- {med}")
                            
                            st.subheader("⚠️ Indicadores de Riesgo")
                            for r in resultado.get("indicadores_riesgo", []): st.write(f"- {r}")
                            
                except Exception as e:
                    st.error(f"Ocurrió un error en el procesamiento: {e}")
