"""Generate a source-grounded PDF with computed file and line references."""
from pathlib import Path
from html import escape
import textwrap
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted, KeepTogether

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf/PARCOURS_CODE_FRONTEND_BACKEND.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
for name,file in [('Arial','arial.ttf'),('ArialBold','arialbd.ttf'),('Code','consola.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
styles={
 'title':ParagraphStyle('title',fontName='ArialBold',fontSize=23,leading=28,spaceAfter=16),
 'h1':ParagraphStyle('h1',fontName='ArialBold',fontSize=18,leading=22,spaceAfter=12),
 'h2':ParagraphStyle('h2',fontName='ArialBold',fontSize=11.5,leading=15,spaceBefore=10,spaceAfter=5,keepWithNext=True),
 'body':ParagraphStyle('body',fontName='Arial',fontSize=10,leading=14,spaceAfter=7),
 'ref':ParagraphStyle('ref',fontName='Code',fontSize=8.5,leading=11,textColor=colors.HexColor('#4b5563'),spaceAfter=7,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='Arial',fontSize=9,leading=12,spaceAfter=0),
 'head':ParagraphStyle('head',fontName='ArialBold',fontSize=9,leading=12),
 'code':ParagraphStyle('code',fontName='Code',fontSize=8.2,leading=11,spaceAfter=9),
}
story=[]
sources={}
def lines(file):
    path=ROOT/file
    if not path.is_file():raise FileNotFoundError(path)
    sources[file]=path
    return path.read_text(encoding='utf-8-sig').splitlines()
def number(file,needle):
    for i,line in enumerate(lines(file),1):
        if needle in line:return i
    raise ValueError(f'Unknown locator {file}: {needle}')
def p(text):story.append(Paragraph(escape(text).replace(' ?', '&#160;?'),styles['body']))
def h(text):story.append(Paragraph(escape(text),styles['h2']))
def page(title):
    if story:story.append(PageBreak())
    story.append(Paragraph(escape(title),styles['h1']))
def ref(file,needle=None):
    content=lines(file)
    label=file+(f' : ligne {number(file,needle)}' if needle else f' : {len(content)} '+('ligne' if len(content)==1 else 'lignes'))
    story.append(Paragraph(f'<link href="{escape((ROOT/file).as_uri(),quote=True)}">{escape(label)}</link>',styles['ref']))
def file_info(file,description,needle=None):
    ref(file,needle);p(description)
def table(headers,rows,widths):
    data=[[Paragraph(escape(str(v)),styles['head']) for v in headers]]
    data.extend([[Paragraph(escape(str(v)).replace(' ?', '&#160;?'),styles['cell']) for v in row] for row in rows])
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9e9ec')),
       ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
       ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
       ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.append(t);story.append(Spacer(1,9))
def code(file,needle,count):
    start=number(file,needle);data=lines(file)[start-1:start-1+count]
    rows=[]
    for i,line in enumerate(data,start):
        prefix=f'{i:3}  '
        parts=textwrap.wrap(line,81-len(prefix),replace_whitespace=False,drop_whitespace=False) or ['']
        rows.extend([(prefix if j==0 else '     ')+part for j,part in enumerate(parts)])
    story.append(Preformatted('\n'.join(rows),styles['code']))
def locate(file,needle):return file+' : '+str(number(file,needle))

story.append(Paragraph('Parcours du code du frontend au backend',styles['title']))
p('Guide de préparation à la présentation chez l’encadreur. Il suit les fichiers réellement présents dans PROJECT et explique qui appelle qui, quelles données circulent et où les résultats sont enregistrés. Le document complète le guide des écrans ; il ne décrit pas une architecture future comme si elle existait déjà.')
h('Le dossier à ouvrir dans l’éditeur')
story.append(Paragraph(escape(str(ROOT)),styles['ref']))
p('Tous les chemins courts de ce PDF sont relatifs à ce dossier. Par exemple, frontend/src/App.tsx désigne le fichier App.tsx dans PROJECT/frontend/src. Les références de fichiers sont cliquables dans les lecteurs PDF qui autorisent l’ouverture de fichiers locaux. Sinon, ouvrir le fichier dans l’éditeur et utiliser Ctrl+G pour atteindre la ligne indiquée.')
p('Repères vérifiés sur le code du 9 octobre 2026. Les numéros de ligne peuvent changer après une modification. Le nom de la fonction ou du composant reste un second repère. Certains composants JSX occupent de longues lignes : utiliser aussi Ctrl+F pour retrouver le bouton ou le texte d’écran.')
h('Le parcours principal')
table(['N','Fichier à suivre','Rôle'],[
('1','frontend/src/main.tsx','Démarre React dans la page HTML.'),
('2','frontend/src/App.tsx','Charge la session, les données et les écrans.'),
('3','frontend/src/forms.tsx','Prépare et envoie la photographie.'),
('4','frontend/src/api.ts','Effectue les appels HTTP vers /api.'),
('5','backend/app/main.py','Valide la demande et crée les enregistrements.'),
('6','backend/app/jobs.py','Exécute le traitement en arrière-plan.'),
('7','backend/app/segmentation.py','Lance YOLO et écrit les masques.'),
('8','frontend/src/AnalysisDetail.tsx','Affiche les résultats renvoyés par le serveur.')],[35,210,236])
h('Une distinction à retenir')
p('Le frontend ne lance pas directement le modèle .pt et ne se connecte pas directement à PostgreSQL. Il envoie des requêtes HTTP à FastAPI. Le backend contrôle les droits, écrit en base et appelle le moteur de segmentation. Le navigateur reçoit des objets JSON et des URLs de fichiers protégés.')

page('Le démarrage du frontend et les échanges HTTP')
file_info('frontend/index.html','Point d’entrée HTML. Le conteneur root reçoit l’application React ; le script source démarre main.tsx. Le dossier dist contient ensuite le résultat de la compilation, pas les fichiers à modifier au quotidien.')
file_info('frontend/src/main.tsx','Crée la racine React, affiche App dans React.StrictMode et importe les styles Leaflet, style.css et sidebar.css. C’est le premier fichier TypeScript exécuté côté interface.','ReactDOM.createRoot')
file_info('frontend/src/api.ts','La fonction api<T> préfixe le chemin avec /api, appelle fetch et transmet les cookies de même origine. Elle interprète les erreurs du serveur via ApiError. json prépare une requête JSON ; dateLabel et numberLabel ne font que formater l’affichage.','export async function api')
code('frontend/src/api.ts','export async function api',9)
p('Exemple : api("/workspace") devient une requête vers /api/workspace. Pour importer une image, api reçoit un FormData : on laisse le navigateur définir le multipart et sa frontière. Pour lancer une analyse, json("POST", {confidence}) prépare un corps JSON.')
file_info('frontend/src/types.ts','Décrit les structures TypeScript : User, Observation, Analysis, Result, Instance, Review, Settings, ModelInfo, Workspace et Sample. Ces types aident à vérifier le code à la compilation ; ils ne remplacent pas la validation des demandes par le serveur.','export type Observation')
file_info('frontend/vite.config.ts','Active React et Tailwind. En développement, le proxy envoie /api vers le backend local 8001. Dans la version compilée utilisée pour la présentation, FastAPI sert directement frontend/dist.','export default')
file_info('frontend/package.json','Déclare les dépendances et les commandes dev, build et preview. npm run build exécute la vérification TypeScript puis produit les fichiers compilés avec Vite.')
h('À expliquer')
p('Le navigateur construit l’interface, puis api.ts sert de pont HTTP. Un type TypeScript est un contrat de code ; la protection réelle des entrées se trouve côté FastAPI et Pydantic.')

page('App la navigation et les styles')
file_info('frontend/src/App.tsx','Composant central : possède l’utilisateur, le workspace, les filtres, la page courante, les messages et l’ouverture de l’import. Les composants enfants reçoivent leurs données et des callbacks.','export default function App')
table(['Repère dans App.tsx','Fonctionnement'],[
(str(number('frontend/src/App.tsx','function readRoute'))+' - readRoute','Lit location.hash : #dashboard ou #observations/identifiant. Le fragment après # n’est pas une route HTTP envoyée au serveur.'),
(str(number('frontend/src/App.tsx','const refresh='))+' - refresh','GET /api/workspace puis setWorkspace. En cas de 401, retire l’utilisateur de l’état de l’interface.'),
(str(number('frontend/src/App.tsx',"api<{initialized:boolean}>('/status')"))+' - premier effet','GET /api/status puis /api/auth/me si la base est initialisée.'),
(str(number('frontend/src/App.tsx','setInterval'))+' - actualisation','Recharge le workspace toutes les 1,5 seconde lorsqu’une analyse est queued ou running.'),
(str(number('frontend/src/App.tsx','function go'))+' - go et open','Change la page et ouvre un dossier ; open peut mémoriser une analyse historique précise.'),
(str(number('frontend/src/App.tsx','async function onCreated'))+' - onCreated','Après import, recharge, ouvre le dossier et demande l’analyse si la case automatique est cochée.')],[170,311])
p('Les tableaux de bord, listes d’observations, historique, vérifications, modèle et carte sont rendus conditionnellement dans App.tsx. Les filtres de date, quartier et recherche sont calculés dans le navigateur à partir du workspace. Le filtre de date s’applique à created_at, la date d’ajout.')
file_info('frontend/src/Sidebar.tsx','Affiche les liens reçus via items, les groupes Navigation et Configuration, le compte et les icônes Lucide. onNavigate revient vers go dans App ; onToggle réduit la barre. Le composant gère lui-même le menu du compte et sa fermeture par clic extérieur ou Échap.','export default function Sidebar')
file_info('frontend/src/style.css','Styles généraux : panneaux, formulaires, états, tableau de bord, résultat, carte et adaptation aux différentes tailles d’écran.')
file_info('frontend/src/sidebar.css','Styles de la nouvelle navigation : largeur 248 px, mode réduit 68 px, état actif, groupes et pied de compte. main.tsx importe ce fichier après style.css afin d’appliquer les règles spécifiques.')
h('À expliquer')
p('Les écrans partagent un état central. Cliquer sur un menu change le hash et le rendu React ; cela ne relance pas un entraînement ou un calcul YOLO.')

page('forms les trois familles de formulaires')
ref('frontend/src/forms.tsx')
h('AuthScreen la connexion')
ref('frontend/src/forms.tsx','export function AuthScreen')
p('submit empêche l’envoi HTML classique avec preventDefault, lit les champs via FormData puis construit un objet. Selon initialized, il appelle POST /api/auth/login ou /api/auth/setup. En cas de succès, onLogin transmet l’utilisateur à App ; le backend a également posé le cookie de session.')
h('UploadModal la photographie')
ref('frontend/src/forms.tsx','export function UploadModal')
p('file contient le fichier choisi. Un effet crée une URL temporaire pour son aperçu puis la libère. examples charge GET /api/samples. chooseSample récupère la photo exemple, la convertit en File et renseigne son titre et ses notes de provenance.')
ref('frontend/src/forms.tsx',"values.set('image',file)")
p('submit vérifie qu’une photo est choisie et contrôle 15 Mo côté client. Le FormData contient les champs et le fichier image. La case analyze est retirée du corps envoyé : elle sert uniquement à décider ensuite de lancer une seconde requête d’analyse. Les coordonnées et la date vides sont retirées. POST /api/observations renvoie l’observation ; onCreated dans App poursuit le parcours.')
h('SettingsPage les paramètres et les comptes')
ref('frontend/src/forms.tsx','export function SettingsPage')
table(['Fonction interne','Route envoyée','Rôle'],[
('save','PUT /api/settings','Enregistre nom, ville et seuil par défaut, puis recharge le workspace.'),
('password','PUT /api/auth/password','Envoie le mot de passe actuel et le nouveau ; vide le formulaire au succès.'),
('addUser','POST /api/users','Crée un compte puis recharge GET /api/users pour la liste.'),
('useEffect de chargement','GET /api/users','Charge les comptes uniquement pour un administrateur.')],[85,160,236])
h('Les validations existent à deux endroits')
p('Les attributs HTML required, minLength et les contrôles React aident l’utilisateur. Ils sont contournables par une requête manuelle. Le backend revalide les tailles, les champs et les permissions. Une case masquée ou un bouton absent ne constitue donc pas la protection principale.')

page('Les composants de consultation et le dossier')
ref('frontend/src/components.tsx')
table(['Composant et ligne','Fonction'],[
('Status : '+str(number('frontend/src/components.tsx','export function Status')),'Traduit none, queued, running, completed et failed en badges.'),
('ReviewStatus : '+str(number('frontend/src/components.tsx','export function ReviewStatus')),'Affiche la dernière décision humaine ; elle est distincte du statut technique.'),
('Empty : '+str(number('frontend/src/components.tsx','export function Empty')),'Affiche un état vide avec une icône et une explication.'),
('Modal : '+str(number('frontend/src/components.tsx','export function Modal')),'Ouvre un dialogue HTML et gère son annulation ou un clic extérieur.'),
('SearchField : '+str(number('frontend/src/components.tsx','export function SearchField')),'Champ contrôlé : sa valeur et son callback appartiennent au parent.'),
('ObservationTable : '+str(number('frontend/src/components.tsx','export function ObservationTable')),'Affiche les observations, appelle onOpen et gère les pages de dix lignes ; cinq en mode compact.'),
('ObservationMap : '+str(number('frontend/src/components.tsx','export function ObservationMap')),'Crée Leaflet, dessine les positions, adapte les limites et ouvre un dossier depuis un point.')],[165,316])
file_info('frontend/src/AnalysisDetail.tsx','Composant du dossier : reçoit row, user, le seuil, la disponibilité du modèle et les callbacks. analysisId sélectionne une analyse ; mode choisit original, overlay ou mask ; zoom et confidence sont des états locaux.','export default function AnalysisDetail')
ref('frontend/src/AnalysisDetail.tsx','async function run')
p('run appelle POST /api/observations/{id}/analyses, sélectionne l’identifiant renvoyé, revient à Original puis demande au parent de recharger les données. La requête crée une tâche ; elle ne contient pas le résultat final.')
ref('frontend/src/AnalysisDetail.tsx','async function review')
p('review appelle POST /api/analyses/{id}/reviews avec decision et comment. onChange recharge le workspace. Le formulaire de vérification est disponible pour administrateur et vérificateur.')
ref('frontend/src/AnalysisDetail.tsx','const image=')
p('Le champ image choisit row.image_url, analysis.overlay_url ou analysis.mask_url. Le navigateur télécharge ces fichiers via des routes protégées. Le même composant rend le nombre d’instances, la couverture, la durée, le tableau des objets et les empreintes. Les exports utilisent des liens de téléchargement directs.')

page('Les premiers fichiers du backend')
file_info('backend/app/config.py','Calcule ROOT et DATA, charge .env, lit DATABASE_URL, JOB_MODE et REDIS_URL, et définit MAX_BYTES et MAX_PIXELS. Les dossiers nécessaires sont créés. Les secrets de .env ne doivent pas être montrés pendant la présentation.','ROOT =')
file_info('backend/app/main.py','Crée l’application FastAPI, les routes HTTP et les modèles Pydantic. lifespan vérifie l’accès au schéma et appelle jobs.recover au démarrage. browser_security contrôle l’origine des mutations et ajoute des en-têtes de protection.','app = FastAPI')
ref('backend/app/main.py','def workspace')
p('workspace charge les comptes, vérifications, analyses et observations. review_dict, analysis_dict et observation_dict transforment les objets de base en réponses JSON et fabriquent les URLs de fichiers. settings_dict fournit les paramètres. Le frontend reçoit ainsi un objet Workspace complet.')
file_info('backend/app/auth.py','Regroupe le hachage, la comparaison de mot de passe, la lecture de session, les rôles et la création de cookie. current_user est injecté dans les routes via Depends ; require_role limite les actions.','def current_user')
table(['Fonction et ligne dans auth.py','Ce qu’elle vérifie ou produit'],[
('hash_password : '+str(number('backend/app/auth.py','def hash_password')),'Sel aléatoire et hachage scrypt, jamais stockage du mot de passe en clair.'),
('check_password : '+str(number('backend/app/auth.py','def check_password')),'Recalcule le hachage et compare avec hmac.compare_digest.'),
('current_user : '+str(number('backend/app/auth.py','def current_user')),'Cookie waste_session, empreinte en base, expiration et compte actif.'),
('require_role : '+str(number('backend/app/auth.py','def require_role')),'Refuse une action avec HTTP 403 si le rôle n’est pas autorisé.'),
('start_session : '+str(number('backend/app/auth.py','def start_session')),'Jeton aléatoire, empreinte en base, cookie HttpOnly SameSite strict valable douze heures.')],[175,306])
p('POST /api/auth/login vérifie le compte et limite les tentatives. POST /api/auth/setup n’est autorisé que pour une base sans compte et crée l’administrateur. GET /api/auth/me renvoie l’utilisateur actuel. POST /api/auth/logout retire sa session. Les contrôles d’authentification ne sont pas exécutés dans le moteur YOLO : ils précèdent les actions métier.')
file_info('backend/app/__init__.py','Fichier d’identification du paquet Python app. Il ne contient pas le moteur d’analyse.')

page('Le parcours exact de l’importation')
h('Le clic jusqu’à la réponse HTTP 201')
table(['N','Repère à ouvrir','Données et opération'],[
('1',locate('frontend/src/forms.tsx',"values.set('image',file)"),'Le FormData porte image, title, neighborhood, location, notes et les champs facultatifs connus.'),
('2',locate('frontend/src/api.ts','export async function api'),'fetch envoie le corps multipart à /api/observations avec la session.'),
('3',locate('backend/app/main.py','async def create_observation'),'FastAPI lit UploadFile et Form, puis impose un rôle administrateur ou agent.'),
('4',locate('backend/app/main.py','raw = await image.read'),'Contrôle de taille, image décodable, format JPEG PNG WebP et maximum de 20 millions de pixels.'),
('5',locate('backend/app/main.py','normalized = ImageOps'),'GPS éventuel, orientation EXIF et conversion RGB.'),
('6',locate('backend/app/main.py',"normalized.save(path"),'Écriture JPEG normalisée, original .source et calcul des empreintes SHA256.'),
('7',locate('backend/app/main.py','row = Observation'),'Création de la ligne observations en transaction ; observation_dict prépare la réponse.'),
('8',locate('frontend/src/App.tsx','async function onCreated'),'Réception du JSON, recharge du registre, ouverture du dossier et éventuelle demande d’analyse.')],[30,220,231])
h('Les destinations de stockage')
p('data/originals/{observation_id}.jpg contient la version normalisée. data/originals/{observation_id}.source conserve les octets importés. PostgreSQL conserve les champs de contexte, dimensions, identifiant du créateur et empreintes. Une erreur de transaction supprime les deux fichiers créés pour cet import.')
h('Ce que la requête ne fait pas')
p('Le backend ne reçoit pas le choix analyze : le frontend l’a retiré du FormData. L’importation et l’analyse sont deux demandes distinctes. Le serveur peut donc avoir enregistré une photo même si la demande d’analyse suivante échoue. L’interface signale ce cas et permet de relancer depuis le dossier.')
h('Un identifiant n’est pas le titre')
p('Le backend crée un UUID pour chaque observation. Les chemins de données utilisent cet identifiant, pas le nom saisi par l’utilisateur. L’analyse possède son propre UUID. C’est ce qui permet de conserver plusieurs traitements pour une même photographie sans écraser les résultats précédents.')

page('La file de traitement et le moteur YOLO')
ref('backend/app/main.py','def analyze')
p('analyze contrôle le rôle, la disponibilité du modèle et l’existence de l’observation. Il refuse une autre analyse pending sur la même photo et limite la file à vingt traitements. Une ligne Analysis avec status queued est créée et validée en base, puis jobs.submit est appelé. La réponse HTTP 202 signifie tâche acceptée, pas calcul terminé.')
file_info('backend/app/jobs.py','En mode local, submit utilise un ThreadPoolExecutor de un worker. run_analysis passe queued à running, appelle predict puis enregistre completed et result_json, ou failed en cas d’erreur. recover reprend les tâches encore queued et marque les traitements running interrompus comme failed.','def run_analysis')
code('backend/app/jobs.py','def run_analysis',17)
file_info('backend/app/segmentation.py','model_config lit active.json et vérifie le chemin des poids. model_status fournit la configuration visible. load_model vérifie SHA256 et classes, puis charge une seule fois YOLO dans un verrou.','def load_model')
ref('backend/app/segmentation.py','def predict')
p('predict lit la photo avec OpenCV, appelle model.predict avec conf, imgsz=960, device=cpu et retina_masks=True. Pour chaque instance, il recueille classe, confiance, boîte et masque. mask_union forme une image binaire en conservant les trous et sans compter deux fois les pixels superposés.')
p('Le moteur compose overlay.jpg, écrit mask.png et result.json, et calcule la couverture en pixels. Les contours et les couleurs facilitent la visualisation ; ils ne prouvent pas une bonne classification. La durée mesurée commence après load_model et ne correspond pas au temps total d’attente utilisateur.')
file_info('backend/app/worker.py','Variante Celery : analyze_task appelle le même run_analysis via un broker Redis. Ce fichier est utilisé seulement si JOB_MODE vaut celery. La démonstration Windows utilise la variante locale ; la configuration Celery n’a pas été exécutée sur ce PC.','def analyze_task')

page('Le retour vers l’écran et les exports')
h('La progression est récupérée par actualisation')
ref('frontend/src/App.tsx','setInterval')
p('Après le POST, App détecte une analyse queued ou running et relance GET /api/workspace toutes les 1,5 seconde. Il n’y a pas de WebSocket dans cette version. jobs.py met à jour la base ; workspace et analysis_dict relisent les résultats ; setWorkspace provoque le nouveau rendu React.')
ref('backend/app/main.py','def analysis_dict')
p('analysis_dict décode result_json et prépare overlay_url et mask_url. AnalysisDetail utilise ces URLs pour afficher la superposition et le masque. Changer de vue ne recalcule pas YOLO ; cela change le fichier téléchargé et affiché.')
table(['Route HTTP','Fonction dans main.py','Utilisation'],[
('GET /api/observations/{key}/image','image_file : '+str(number('backend/app/main.py','def image_file')),'Photo normalisée, session requise.'),
('GET /api/analyses/{key}','analysis : '+str(number('backend/app/main.py','def analysis(')),'Consultation d’un traitement.'),
('GET /api/analyses/{key}/files/{kind}','result_file : '+str(number('backend/app/main.py','def result_file')),'kind = overlay, mask ou json ; analyse terminée requise.'),
('POST /api/analyses/{key}/reviews','review : '+str(number('backend/app/main.py','def review(')),'Ajout d’une décision, pas modification du masque.'),
('GET /api/observations/{key}/export','export_observation : '+str(number('backend/app/main.py','def export_observation')),'Dossier JSON avec analyses et vérifications.'),
('GET /api/export/csv','export_all : '+str(number('backend/app/main.py','def export_all')),'Registre CSV complet.'),
('GET /api/export/geojson','export_all : '+str(number('backend/app/main.py','def export_all')),'Positions réellement renseignées.')],[215,130,136])
h('Un journal de décisions séparé')
ref('frontend/src/AnalysisDetail.tsx','async function review')
p('Le formulaire transmet accepted, rejected ou uncertain et un commentaire. main.py exige un rôle admin ou reviewer et une analyse completed. Une nouvelle ligne Review est ajoutée. Les anciennes décisions restent conservées ; latest_review est la dernière. Les compteurs À vérifier utilisent cette dernière décision sur la dernière analyse de chaque observation.')
p('Les exports sont des liens directs vers /api ; leur téléchargement n’emprunte pas obligatoirement api.ts. Ils restent protégés par current_user. Les filtres visuels sont locaux : les exports CSV et GeoJSON portent sur le registre entier.')

page('Localisation modèle et configuration')
h('Le trajet des coordonnées')
ref('backend/app/main.py','def exif_coordinates')
p('Les champs latitude et longitude proviennent de forms.tsx. create_observation impose la paire complète, donne priorité à la saisie manuelle et lit le GPS EXIF si la paire est absente. Observation conserve latitude, longitude et coordinate_source. workspace les renvoie ; App filtre les photos localisées et les passe à ObservationMap.')
ref('frontend/src/components.tsx','export function ObservationMap')
p('Le premier effet crée Leaflet et le fond OpenStreetMap. Le second vide et recrée les points quand rows change, puis utilise fitBounds. Un clic sur Ouvrir l’observation appelle le callback du parent. Les coordonnées localisent la photo ; YOLO ne fournit pas une adresse depuis les masques.')
ref('frontend/src/components.tsx','referrerPolicy')
p('La couche de tuiles possède referrerPolicy strict-origin-when-cross-origin. Elle transmet l’origine locale requise par OpenStreetMap malgré la politique globale same-origin du serveur. Les autres échanges de l’application conservent leurs protections. Le fond nécessite Internet.')
h('La page Modèle est surtout alimentée par le workspace')
ref('backend/app/segmentation.py','def model_status')
file_info('models/active.json','Déclare les poids actifs, nom, provenance, révision, classes, empreinte et limites. models/waste-yolo11s-seg.pt est le fichier de poids exécuté, pas un fichier JavaScript. Si models/evaluation.json existe et correspond au SHA du modèle actif, model_status expose ses métriques locales.')
p('Le rendu Modèle YOLO se trouve dans App.tsx. Les métriques externes TACO sont explicitement séparées des métriques locales. Le mode détaillé par découpes et l’édition manuelle de masques sont des propositions, pas des branches de code déjà actives.')
h('Paramètres comptes et exemples côté serveur')
table(['Route','Repère dans main.py'],[
('GET et PUT /api/settings','get_settings : '+str(number('backend/app/main.py','def get_settings'))+' ; update_settings : '+str(number('backend/app/main.py','def update_settings'))),
('PUT /api/auth/password','password : '+str(number('backend/app/main.py','def password('))),
('GET et POST /api/users','users : '+str(number('backend/app/main.py','def users('))+' ; create_user : '+str(number('backend/app/main.py','def create_user'))),
('GET /api/samples et /api/samples/{key}','samples : '+str(number('backend/app/main.py','def samples('))+' ; sample_file : '+str(number('backend/app/main.py','def sample_file'))),
('GET /api/status et /api/health','status : '+str(number('backend/app/main.py','def status('))+' ; health : '+str(number('backend/app/main.py','def health(')))],[275,206])

page('La base les migrations et les fichiers')
file_info('backend/app/database.py','Crée engine à partir de DATABASE_URL et Session pour les transactions. Les classes SQLAlchemy décrivent les tables ; les créer dans le fichier Python ne remplace pas la migration du schéma.','engine =')
table(['Classe et ligne','Table','Données importantes'],[
('User : '+str(number('backend/app/database.py','class User')),'users','Nom, login, hachage, rôle et actif.'),
('LoginSession : '+str(number('backend/app/database.py','class LoginSession')),'login_sessions','Empreinte de jeton, utilisateur et expiration.'),
('Observation : '+str(number('backend/app/database.py','class Observation')),'observations','Photo référencée par UUID, contexte, GPS, dimensions et empreintes.'),
('Analysis : '+str(number('backend/app/database.py','class Analysis')),'analyses','Observation liée, auteur, état, seuil, dates, erreur et result_json.'),
('Review : '+str(number('backend/app/database.py','class Review')),'reviews','Analyse liée, décision, commentaire, vérificateur et date.'),
('Setting : '+str(number('backend/app/database.py','class Setting')),'settings','Paramètres sous forme clé et valeur.')],[115,95,271])
p('Les relations sont assurées par des clés étrangères : une Analysis référence une Observation ; une Review référence une Analysis. Les créateurs et vérificateurs référencent des User. L’observation possède plusieurs analyses ; une analyse possède plusieurs vérifications. Ces liens expliquent pourquoi les journaux peuvent être conservés sans écraser les traitements.')
file_info('backend/migrations/env.py','Configure Alembic avec Base.metadata et la connexion de l’application, puis exécute les migrations.','def online')
file_info('backend/migrations/versions/0001_initial.py','Première migration enregistrée : décrit les tables et index de départ. start.ps1 applique alembic upgrade head avant de lancer FastAPI.')
file_info('backend/alembic.ini','Configuration d’Alembic et chemin du dossier de migrations. Elle est passée à la commande avec -c.')
h('Les chemins de données')
table(['Chemin dans PROJECT','Contenu'],[
('data/originals/{observation_id}.jpg','Photo normalisée utilisée par OpenCV et YOLO.'),
('data/originals/{observation_id}.source','Fichier initial importé, conservé pour traçabilité.'),
('data/results/{analysis_id}/overlay.jpg','Superposition colorée.'),
('data/results/{analysis_id}/mask.png','Union des masques en pixels.'),
('data/results/{analysis_id}/result.json','Résultat détaillé du traitement.'),
('runtime/postgres et backups','Données du cluster local et archives de sauvegarde.')],[275,206])
p('DATA est configurable par WASTE_DATA_DIR. Une sauvegarde complète doit conserver PostgreSQL et les fichiers image.')

page('Lancement et outils complémentaires')
file_info('LANCER.cmd','Point de lancement par double-clic. Appelle le script PowerShell start.ps1.')
file_info('start.ps1','Se place dans PROJECT, prépare PostgreSQL, exécute Alembic, vérifie frontend/dist puis lance Uvicorn app.main:app avec --app-dir backend et le port 8001.')
file_info('install.ps1','Prépare l’environnement Python, les dépendances, le frontend compilé, les poids et les exemples. Sert à l’installation, pas à chaque clic d’analyse.')
table(['Script dans scripts','Rôle'],[
('prepare_database.py','Démarre ou prépare le cluster PostgreSQL local du projet et sa connexion.'),
('download_model.py','Récupère la révision de modèle prévue et les exemples, avec contrôle des poids.'),
('convert_coco.py','Convertit des annotations polygonales COCO en données YOLO segmentées et partitions.'),
('dataset_tools.py','Vérifie les images, annotations, coordonnées et doublons exacts entre partitions.'),
('train.py','Commande d’entraînement à lancer après préparation d’un corpus annoté.'),
('register_model.py','Contrôle et enregistre de nouveaux poids de segmentation dans le manifeste actif.'),
('evaluate.py','Évalue des poids sur une partition de test et écrit un rapport traçable.'),
('backup.py','Archive dump PostgreSQL et fichiers nécessaires à la restauration.'),
('reset_password.py','Outil local de réinitialisation de mot de passe avec invalidation des sessions.')],[170,311])
for name in ['prepare_database.py','download_model.py','convert_coco.py','dataset_tools.py','train.py','register_model.py','evaluate.py','backup.py','reset_password.py']:lines('scripts/'+name)
h('Configuration et tests')
p('.env contient les valeurs locales sensibles ; .env.example présente les variables attendues sans fournir les secrets. backend/requirements.txt et frontend/package-lock.json documentent les dépendances. Dockerfile et compose.yaml décrivent une variante de déploiement avec PostgreSQL, Redis et worker, non exécutée sur le PC de démonstration.')
ref('backend/app/main.py','def spa')
p('À la fin de main.py, /assets sert les fichiers compilés et spa renvoie frontend/dist/index.html. Une route API inconnue reste une erreur 404, au lieu de renvoyer silencieusement l’interface.')
p('tests contient les tests automatisés de logique et d’API. docs/qa contient les contrôles navigateur et les preuves techniques ; ces scripts ne sont pas le moteur utilisé à chaque analyse. Le corpus de Goma, son entraînement et son évaluation scientifique restent à réaliser.')

page('Ordre de lecture et repères pour expliquer le code')
h('Lire la chaîne dans cet ordre')
table(['N','Fichier et repère','Question à laquelle il répond'],[
('1',locate('frontend/src/main.tsx','ReactDOM.createRoot'),'Où React démarre-t-il ?'),
('2',locate('frontend/src/App.tsx','const refresh='),'D’où viennent les données des écrans ?'),
('3',locate('frontend/src/forms.tsx',"values.set('image',file)"),'Comment le formulaire envoie-t-il la photo ?'),
('4',locate('frontend/src/api.ts','export async function api'),'Comment la demande devient-elle une requête HTTP ?'),
('5',locate('backend/app/main.py','async def create_observation'),'Où le serveur contrôle-t-il et enregistre-t-il l’image ?'),
('6',locate('backend/app/main.py','def analyze'),'Où l’analyse est-elle mise en file ?'),
('7',locate('backend/app/jobs.py','def run_analysis'),'Qui exécute le calcul et change les états ?'),
('8',locate('backend/app/segmentation.py','def predict'),'Où YOLO produit-il les masques ?'),
('9',locate('backend/app/main.py','def analysis_dict'),'Comment les résultats redeviennent-ils du JSON ?'),
('10',locate('frontend/src/AnalysisDetail.tsx','const image='),'Comment Original Segmentation Masque sont-ils affichés ?')],[30,280,171])
h('Où chercher si quelque chose ne fonctionne pas')
p('Connexion : forms.tsx, route login et auth.py. Import : submit de UploadModal et create_observation. Analyse bloquée : analyze, jobs.py et journal serveur. Masque absent : segmentation.py, fichier dans data/results et route result_file. Carte sans point : coordonnées dans Observation puis ObservationMap. Carte bloquée : requêtes des tuiles et referrerPolicy. Chiffre inattendu : filtres et calculs dans App.tsx.')
h('Ce que je peux dire à l’encadreur')
p('« J’ai séparé l’affichage du calcul. React envoie une photo à FastAPI ; le serveur la contrôle et l’enregistre. Une tâche lance YOLO puis OpenCV prépare les masques. PostgreSQL garde l’état et les informations, et l’interface récupère le résultat. Une vérification humaine est ensuite ajoutée séparément. »')
p('« Les fichiers que je présente correspondent au parcours testé. Le modèle est externe ; l’intégration fonctionne. Je dois encore constituer les annotations de terrain et mesurer les performances sur un jeu de test indépendant. »')
h('Utiliser les repères sans modifier par hasard')
p('Ouvrir les fichiers pour expliquer leur rôle. Ne pas modifier .env, les poids ou la base pour une simple démonstration. Après un changement frontend, une compilation est nécessaire pour actualiser dist. Après un changement Python sans mode reload, le serveur doit être redémarré. Les fichiers de ce guide sont des repères de lecture, pas des instructions de déploiement.')

def footer(canvas,document):
    canvas.saveState();canvas.setFont('Arial',8);canvas.setFillColor(colors.HexColor('#4b5563'))
    canvas.drawString(54,A4[1]-32,'Déchets urbains   Parcours du code vérifié le 9 octobre 2026')
    canvas.drawRightString(A4[0]-54,30,'Page '+str(document.page))
    canvas.restoreState()

pdf=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=57,rightMargin=57,topMargin=56,bottomMargin=48,
    title='Parcours du code du frontend au backend',author='',subject='Guide de lecture du code de PROJECT')
pdf.build(story,onFirstPage=footer,onLaterPages=footer)
print(str(OUT));print('Sources vérifiées : '+str(len(sources)))
