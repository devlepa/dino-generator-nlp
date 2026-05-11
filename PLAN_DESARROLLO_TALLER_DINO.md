# Plan paso a paso - Taller Generador de Dinosaurios

Este plan traduce el PDF del taller en una ruta de trabajo ejecutable para un equipo. La idea es entregar un sitio web desplegado en AWS que integre:

- Generacion de nombres con un modelo de lenguaje a nivel de caracteres.
- Descripciones generadas con Ollama en SageMaker.
- Imagenes generadas con un modelo liviano de difusion en Colab o entorno equivalente.
- Integracion web con boton "Nuevo Dinosaurio".
- Endpoints expuestos por ngrok, no APIs publicas directas.
- Repositorio GitHub organizado para trabajo colaborativo.

## 0. Reglas del proyecto

1. No exponer APIs directamente a internet.
   - Ollama debe correr en SageMaker, pero el acceso externo debe hacerse por tunel HTTP de ngrok.
   - El servicio de difusion debe correr en Colab/local/entorno equivalente y exponerse por ngrok.
   - El frontend desplegado en AWS solo consume URLs de ngrok configurables.

2. Medir recursos desde el primer dia.
   - Crear presupuesto en AWS Budgets antes de levantar SageMaker.
   - Usar tags en recursos: `Project=DinoGenerator`, `Course=NLP`, `Owner=equipo`.
   - Encender SageMaker solo cuando se use y apagarlo al terminar.
   - Registrar horas de uso, instancia, almacenamiento y modelos descargados.

3. No usar APIs externas para la Parte 2.
   - Las descripciones deben salir de un LLM local con Ollama.
   - No usar OpenAI, Gemini API, Claude API ni servicios equivalentes.

4. Guardar solo lo necesario en Git.
   - Subir codigo, notebooks limpios, scripts, resultados pequeños y documentacion.
   - No subir modelos pesados, `.venv`, credenciales, tokens de ngrok ni archivos generados enormes.

## 1. Arquitectura propuesta

```text
Usuario
  |
  v
Frontend web en AWS Amplify Hosting
  |
  |-- Generador de nombres:
  |     Opcion recomendada: modelo/export ligero cargado en el navegador
  |     Alternativa: endpoint interno con Lambda, si el curso lo permite
  |
  |-- Descripcion:
  |     HTTPS ngrok -> SageMaker Notebook m5.xlarge -> Docker -> Ollama
  |
  |-- Imagen:
        HTTPS ngrok -> Google Colab/local GPU -> FastAPI/Gradio -> modelo diffusion
```

### Decision recomendada

Para reducir costos y evitar exponer una API propia en AWS, el generador de nombres debe quedar como artefacto liviano consumido por el frontend:

- Entrenar en notebook.
- Exportar vocabulario, pesos o una tabla de probabilidades/modelo pequeno.
- Incluir una funcion `generateName()` en el frontend.
- El boton "Nuevo Dinosaurio" genera nombre localmente, luego llama a Ollama por ngrok, y despues llama a difusion por ngrok.

Si el modelo RNN no se puede ejecutar facilmente en navegador, guardar una lista amplia de nombres generados y usar el frontend para muestrear entre candidatos. Para la sustentacion, mostrar claramente que el entrenamiento si se hizo en notebooks y que los resultados vienen del modelo.

## 2. Estructura del repositorio

Crear esta estructura desde el inicio:

```text
dino-generator/
  README.md
  PLAN_DESARROLLO_TALLER_DINO.md
  .gitignore
  .env.example
  data/
    raw/
      dinos.csv
    processed/
  notebooks/
    01_char_rnn_training.ipynb
    02_ollama_descriptions_sagemaker.ipynb
    03_diffusion_images_colab.ipynb
  src/
    char_model/
      preprocess.py
      train.py
      sample.py
      export_model.py
    services/
      ollama_client.py
      diffusion_client.py
    web/
      package.json
      src/
      public/
  scripts/
    setup_sagemaker_ollama.sh
    sagemaker_lifecycle_on_start.sh
    run_ollama_ngrok.sh
    run_diffusion_ngrok.py
  outputs/
    names/
      generated_names.json
    descriptions/
      dinosaur_descriptions.json
    images/
      manifest.json
  reports/
    model_report.md
    experiment_log.md
    resource_usage.md
```

## 3. Configuracion inicial de GitHub

### 3.1 Crear repositorio

1. Crear un repositorio en GitHub con nombre sugerido: `dino-generator-nlp`.
2. Marcarlo como privado si el grupo no quiere exponer entregables antes de la entrega.
3. Agregar colaboradores desde `Settings > Collaborators`.
4. Clonar en local:

```bash
git clone git@github.com:USUARIO_O_ORG/dino-generator-nlp.git
cd dino-generator-nlp
```

### 3.2 Primer commit base

```bash
git checkout -b setup/project-structure
mkdir -p data/raw data/processed notebooks src/char_model src/services src/web scripts outputs/names outputs/descriptions outputs/images reports
cp /ruta/a/dinos.csv data/raw/dinos.csv
touch README.md .env.example reports/experiment_log.md reports/resource_usage.md
git add .
git commit -m "chore: create project structure"
git push -u origin setup/project-structure
```

Abrir Pull Request hacia `main` y pedir revision de otro integrante.

### 3.3 Reglas de colaboracion

1. Nadie trabaja directo en `main`.
2. Cada tarea se hace en una rama:
   - `feature/char-rnn`
   - `feature/ollama-sagemaker`
   - `feature/diffusion-colab`
   - `feature/web-integration`
   - `docs/report`
3. Todo entra por Pull Request.
4. Usar Issues para dividir el trabajo.
5. Proteger `main` con branch protection:
   - Require pull request before merging.
   - Require approvals.
   - Block force pushes.
   - Require status checks si se agregan tests o lint.

## 4. Control de costos y recursos en AWS

### 4.1 Antes de crear SageMaker

1. Ir a AWS Billing and Cost Management.
2. Crear un AWS Budget mensual.
3. Configurar alertas por correo al 50%, 80% y 100%.
4. Definir un limite acorde a la cuenta educativa.
5. Crear un documento `reports/resource_usage.md` y registrar:
   - Fecha.
   - Servicio usado.
   - Region.
   - Instancia.
   - Hora de inicio.
   - Hora de apagado.
   - Motivo.

Plantilla:

```md
| Fecha | Servicio | Region | Recurso | Inicio | Fin | Horas | Responsable | Nota |
|---|---|---|---|---|---|---:|---|---|
| 2026-05-11 | SageMaker | us-east-1 | ml.m5.xlarge | 14:00 | 16:00 | 2 | Nombre | Ollama + pruebas |
```

### 4.2 Recomendaciones de uso medido

1. Usar SageMaker `m5.xlarge` porque el taller lo pide.
2. Apagar el notebook cuando no este generando descripciones.
3. Evitar dejar ngrok, Docker y Ollama corriendo de noche.
4. Descargar un modelo pequeno en Ollama:
   - `gemma:2b`
   - `qwen2.5:1.5b`
   - `llama3.2:1b`
5. Guardar modelos y datos persistentes dentro de `/home/ec2-user/SageMaker`.
6. No guardar nada importante fuera de `/home/ec2-user/SageMaker`, porque SageMaker no persiste archivos externos a esa carpeta al detener/reiniciar.

## 5. Parte 1 - Generador de caracteres con RNN

### 5.1 Datos

1. Descargar `dinos.csv` desde el enlace del taller.
2. Guardarlo en `data/raw/dinos.csv`.
3. Crear notebook `notebooks/01_char_rnn_training.ipynb`.
4. Crear scripts equivalentes en `src/char_model/` para que el notebook no sea el unico lugar donde vive el codigo.

### 5.2 Preprocesamiento

Implementar:

1. Leer nombres.
2. Convertir a minusculas.
3. Remover espacios innecesarios.
4. Definir tokens:
   - `<PAD>`
   - `<SOS>`
   - `<EOS>`
5. Construir vocabulario caracter a indice.
6. Calcular longitud maxima `T`.
7. Crear pares:

```text
X = [x0, x1, ..., xT-1]
Y = [x1, x2, ..., xT]
```

8. Aplicar padding.
9. Dividir en entrenamiento y validacion.

### 5.3 Modelos a comparar

Entrenar al menos 2 variantes:

1. RNN simple.
2. GRU o LSTM.

Registrar en `reports/experiment_log.md`:

```md
| Exp | Modelo | Embedding | Hidden | Layers | Epochs | Loss train | Loss val | Observaciones |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 001 | GRU | 64 | 128 | 1 | 50 | | | |
```

### 5.4 Muestreo

Implementar generacion con:

1. Temperaturas: `0.7`, `1.0`, `2.5`, `4.0`.
2. Top-k: probar `k=5`, `k=10`, `k=20`.
3. Top-p: probar `p=0.8`, `p=0.9`, `p=0.95`.

Guardar resultados en:

```text
outputs/names/generated_names.json
```

Formato sugerido:

```json
[
  {
    "name": "Aureliraptor",
    "model": "GRU",
    "temperature": 0.7,
    "top_k": 10,
    "top_p": null,
    "score": 4,
    "notes": "Suena plausible, sufijo paleontologico claro."
  }
]
```

### 5.5 Entregable de la Parte 1

1. Seleccionar los 10 mejores nombres.
2. Justificar en 3 a 5 lineas:
   - Que modelo dio mejores nombres.
   - Que temperatura fue mas estable.
   - Como afectaron top-k y top-p la creatividad/coherencia.
3. Agregar curvas de perdida y tabla de experimentos en `reports/model_report.md`.

## 6. Parte 2 - Ollama en SageMaker con ngrok

### 6.1 Crear SageMaker Notebook

1. Abrir Amazon SageMaker.
2. Crear Notebook Instance.
3. Tipo de instancia: `ml.m5.xlarge`.
4. Volumen: elegir el minimo razonable que soporte Docker + modelo Ollama. Recomendado inicial: 30 GB si la cuenta lo permite.
5. IAM Role: el minimo necesario para SageMaker Notebook.
6. Tags:
   - `Project=DinoGenerator`
   - `Course=NLP`
   - `Owner=equipo`

### 6.2 Persistencia de Docker y Ollama

El taller exige que Docker use una ruta persistente dentro de `/home/ec2-user/SageMaker`. Crear lifecycle script `scripts/sagemaker_lifecycle_on_start.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

mkdir -p /home/ec2-user/SageMaker/docker-data
mkdir -p /home/ec2-user/SageMaker/ollama

cat >/etc/docker/daemon.json <<'JSON'
{
  "data-root": "/home/ec2-user/SageMaker/docker-data"
}
JSON

systemctl restart docker
chown -R ec2-user:ec2-user /home/ec2-user/SageMaker/docker-data /home/ec2-user/SageMaker/ollama
```

Notas:

- El lifecycle script corre como root.
- Para comandos que creen archivos de usuario dentro de `/home/ec2-user/SageMaker`, usar `sudo -u ec2-user`.
- No guardar tokens dentro del lifecycle script.

### 6.3 Instalar y ejecutar Ollama con Docker

En SageMaker:

```bash
docker run -d \
  -v /home/ec2-user/SageMaker/ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama
```

Descargar un modelo pequeno:

```bash
docker exec -it ollama ollama pull qwen2.5:1.5b
```

Probar:

```bash
curl http://localhost:11434/api/generate \
  -d '{
    "model": "qwen2.5:1.5b",
    "prompt": "Describe un dinosaurio llamado Aureliraptor en 4 lineas.",
    "stream": false
  }'
```

### 6.4 Exponer Ollama con ngrok

1. Crear cuenta en ngrok.
2. Instalar ngrok en SageMaker.
3. Configurar token:

```bash
ngrok config add-authtoken TU_TOKEN
```

4. Exponer Ollama:

```bash
ngrok http 11434
```

5. Copiar URL HTTPS generada, por ejemplo:

```text
https://xxxxx.ngrok-free.app
```

6. Guardarla en `.env` local, nunca en Git:

```env
OLLAMA_BASE_URL=https://xxxxx.ngrok-free.app
OLLAMA_MODEL=qwen2.5:1.5b
```

### 6.5 Generar descripciones

Crear `notebooks/02_ollama_descriptions_sagemaker.ipynb` o script `src/services/ollama_client.py`.

Prompt base:

```text
Eres un asistente de paleontologia creativa. Genera una descripcion breve para un dinosaurio ficticio.
El nombre debe sonar coherente con patrones reales de dinosaurios, como sufijos -saurus, -raptor, -odon,
-long o -venator, y prefijos de origen griego o latino relacionados con forma, tamano, lugar o comportamiento.

Nombre: {name}

Devuelve JSON con:
- nombre
- significado_posible
- descripcion
- habitat
- rasgos
```

Guardar en:

```text
outputs/descriptions/dinosaur_descriptions.json
```

## 7. Parte 3 - Text-to-Image en Colab o entorno con GPU T4

### 7.1 Crear notebook

Archivo:

```text
notebooks/03_diffusion_images_colab.ipynb
```

Instalar:

```bash
pip install diffusers transformers torch accelerate safetensors fastapi uvicorn pyngrok
```

### 7.2 Seleccionar modelo liviano

Prioridad:

1. `amused/amused-512`, si funciona bien en el entorno.
2. Otro modelo liviano compatible con `diffusers`.
3. Bajar resolucion si hay errores de memoria: 512 o menos.

### 7.3 Servicio de imagenes

Crear un endpoint local en Colab con FastAPI:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ImageRequest(BaseModel):
    name: str
    description: str

@app.post("/generate-image")
def generate_image(req: ImageRequest):
    prompt = f"{req.name}, dinosaur, {req.description}, detailed but lightweight"
    # generar imagen, guardar archivo/base64, retornar URL o base64
    return {"image_base64": "...", "prompt": prompt}
```

Ejecutar:

```bash
uvicorn app:app --host 0.0.0.0 --port 7860
ngrok http 7860
```

Guardar URL en `.env`:

```env
DIFFUSION_BASE_URL=https://yyyyy.ngrok-free.app
```

### 7.4 Generar imagenes de los 10 ejemplos

1. Leer `outputs/descriptions/dinosaur_descriptions.json`.
2. Crear prompt por dinosaurio.
3. Generar una imagen por nombre.
4. Guardar imagenes optimizadas para web.
5. Crear manifest:

```text
outputs/images/manifest.json
```

Formato:

```json
[
  {
    "name": "Aureliraptor",
    "description_id": "aureliraptor",
    "image_path": "outputs/images/aureliraptor.png",
    "prompt": "..."
  }
]
```

## 8. Parte 4 - Sitio web integrado

### 8.1 Secciones obligatorias

El sitio debe tener:

1. Descripcion del modelo.
   - Arquitectura.
   - Preprocesamiento.
   - Metricas.
   - Curvas de aprendizaje.
   - Comparacion de temperatura, top-k y top-p.

2. Seccion de ejemplos.
   - Tabla o tarjetas con 10 nombres.
   - Descripcion generada por Ollama.
   - Imagen generada por difusion.
   - Parametros usados.

3. Seccion interactiva.
   - Boton "Nuevo Dinosaurio".
   - Genera nombre.
   - Llama a Ollama via ngrok.
   - Llama a difusion via ngrok.
   - Muestra nombre, descripcion e imagen.

### 8.2 Variables de entorno del frontend

Crear `.env.example`:

```env
VITE_OLLAMA_BASE_URL=https://example-ollama.ngrok-free.app
VITE_OLLAMA_MODEL=qwen2.5:1.5b
VITE_DIFFUSION_BASE_URL=https://example-diffusion.ngrok-free.app
```

No subir `.env` real.

### 8.3 Manejo de errores

El sitio debe mostrar mensajes claros si:

1. SageMaker esta apagado.
2. ngrok cambio de URL.
3. Ollama tarda demasiado.
4. Colab desconecto la GPU.
5. Difusion no retorna imagen.

### 8.4 Despliegue en AWS

Opcion recomendada: AWS Amplify Hosting conectado a GitHub.

Pasos:

1. Entrar a AWS Amplify.
2. Crear nueva app.
3. Seleccionar GitHub.
4. Autorizar la GitHub App de Amplify solo para este repositorio.
5. Seleccionar rama `main`.
6. Configurar build.
7. Agregar variables de entorno en Amplify:
   - `VITE_OLLAMA_BASE_URL`
   - `VITE_OLLAMA_MODEL`
   - `VITE_DIFFUSION_BASE_URL`
8. Deploy.

Importante:

- Si las URLs gratuitas de ngrok cambian, actualizar variables de entorno y redeploy.
- Para la sustentacion, iniciar SageMaker, Ollama, ngrok, Colab y ngrok antes de abrir el sitio.

## 9. Flujo diario de trabajo colaborativo

### 9.1 Inicio del dia

```bash
git checkout main
git pull origin main
git checkout -b feature/nombre-de-la-tarea
```

### 9.2 Durante el trabajo

```bash
git status
git add archivo1 archivo2
git commit -m "feat: describe change"
git push -u origin feature/nombre-de-la-tarea
```

### 9.3 Pull Request

Cada PR debe incluir:

```md
## Que cambia
- 

## Como probar
- 

## Evidencia
- Screenshot, curva, tabla o salida relevante.

## Riesgos
- 
```

### 9.4 Convencion de commits

Usar mensajes claros:

```text
feat: add GRU name generator
fix: handle ollama timeout
docs: add experiment notes
chore: update dependencies
```

### 9.5 Archivos que no deben subirse

Agregar a `.gitignore`:

```gitignore
.venv/
__pycache__/
.env
.DS_Store
*.pt
*.pth
*.ckpt
*.safetensors
outputs/images/*.png
outputs/images/*.jpg
ngrok.yml
```

Si las imagenes finales son livianas y necesarias para el sitio, se pueden subir a `src/web/public/examples/` optimizadas. Evitar subir lotes grandes.

## 10. Orden recomendado de ejecucion

### Dia 1 - Base y datos

1. Crear repositorio GitHub.
2. Crear estructura del proyecto.
3. Subir `dinos.csv`.
4. Crear Issues por componente.
5. Crear AWS Budget.
6. Definir responsables.

### Dia 2 - Modelo de nombres

1. Implementar preprocesamiento.
2. Entrenar RNN simple.
3. Entrenar GRU/LSTM.
4. Implementar temperatura, top-k y top-p.
5. Generar candidatos.
6. Seleccionar 10 mejores.

### Dia 3 - Ollama en SageMaker

1. Crear SageMaker `ml.m5.xlarge`.
2. Configurar lifecycle script.
3. Instalar Docker/Ollama.
4. Descargar modelo pequeno.
5. Exponer con ngrok.
6. Generar descripciones.
7. Apagar SageMaker al terminar.

### Dia 4 - Difusion

1. Crear notebook Colab.
2. Probar modelo liviano.
3. Crear endpoint local.
4. Exponer con ngrok.
5. Generar imagenes de los 10 nombres.
6. Guardar manifest.

### Dia 5 - Web

1. Crear frontend.
2. Implementar seccion de modelo.
3. Implementar ejemplos.
4. Implementar boton "Nuevo Dinosaurio".
5. Manejar errores.
6. Probar con URLs ngrok.

### Dia 6 - Deploy y evidencia

1. Conectar Amplify con GitHub.
2. Configurar variables de entorno.
3. Desplegar.
4. Grabar evidencia o screenshots.
5. Completar reportes.
6. Revisar costos.

### Dia 7 - Ensayo de sustentacion

1. Encender SageMaker.
2. Iniciar Ollama.
3. Iniciar ngrok para Ollama.
4. Iniciar Colab/difusion.
5. Iniciar ngrok para difusion.
6. Actualizar variables de entorno si cambiaron.
7. Probar sitio desde cero.
8. Ensayar explicacion de arquitectura, costos y experimentos.

## 11. Checklist final de entrega

- [ ] Repositorio GitHub con README claro.
- [ ] `dinos.csv` en `data/raw/`.
- [ ] Notebook de entrenamiento.
- [ ] Codigo de preprocesamiento, entrenamiento y muestreo.
- [ ] Comparacion RNN vs GRU/LSTM.
- [ ] Temperatura, top-k y top-p implementados.
- [ ] 10 nombres seleccionados.
- [ ] Nota comparativa de 3 a 5 lineas.
- [ ] SageMaker `ml.m5.xlarge` usado para Ollama.
- [ ] Docker data-root persistente en `/home/ec2-user/SageMaker`.
- [ ] Lifecycle script documentado.
- [ ] Ollama expuesto con ngrok.
- [ ] Descripciones generadas localmente, sin APIs externas.
- [ ] Notebook de difusion en Colab o entorno equivalente.
- [ ] Imagen para cada uno de los 10 nombres.
- [ ] Servicio de difusion expuesto con ngrok.
- [ ] Sitio web con las 3 secciones requeridas.
- [ ] Boton "Nuevo Dinosaurio" funcional.
- [ ] Sitio desplegado en AWS.
- [ ] `reports/resource_usage.md` completo.
- [ ] Presupuesto de AWS configurado.
- [ ] Sustentacion ensayada.

## 12. Riesgos y mitigaciones

| Riesgo | Mitigacion |
|---|---|
| SageMaker consume presupuesto | Usar Budget, apagar al terminar, registrar horas |
| Ollama en CPU es lento | Usar modelo pequeno y prompts cortos |
| ngrok cambia URL | Guardar variables en `.env`, actualizar Amplify antes de sustentar |
| Colab se desconecta | Generar imagenes base previamente y tener fallback visual |
| Modelo de difusion consume mucha VRAM | Usar modelo liviano, resolucion baja y pocos pasos |
| Frontend falla si endpoint duerme | Mostrar error claro y permitir reintentar |
| Conflictos en Git | Ramas pequenas, PRs frecuentes, Issues por tarea |
| Tokens filtrados | `.env` ignorado, no pegar tokens en notebooks subidos |

## 13. Fuentes oficiales consultadas

- AWS SageMaker Lifecycle Configurations: https://docs.aws.amazon.com/sagemaker/latest/dg/notebook-lifecycle-config.html
- Persistencia en SageMaker Notebook Instances: https://docs.aws.amazon.com/sagemaker/latest/dg/howitworks-create-ws.html
- AWS Budgets: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-create.html
- AWS Amplify con GitHub: https://docs.aws.amazon.com/amplify/latest/userguide/setting-up-GitHub-access.html
- ngrok Free Plan Limits: https://ngrok.com/docs/pricing-limits/free-plan-limits
- Ollama Docker: https://docs.ollama.com/docker
- GitHub Protected Branches: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
