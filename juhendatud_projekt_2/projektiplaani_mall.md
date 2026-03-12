# 🤖 Tehisintellekti rakendamise projektiplaani mall (CRISP-DM)

<br>
<br>


## 🔴 1. Äritegevuse mõistmine
*Fookus: mis on probleem ja milline on hea tulemus?*


### 🔴 1.1 Kasutaja kirjeldus ja eesmärgid
Kellel on probleem ja miks see lahendamist vajab? Mis on lahenduse oodatud kasu? Milline on hetkel eksisteeriv lahendus?

> Kasutajaks on tootmisettevõte. Probleem seisneb selles, et kiirel tootmisliinil (8 toodet iga 7 sekundi järel) on kahel töötajal raske märgata defekte: sildid võivad olla puudu, pakendis võib olla vale toode või sildil on vale info/puuduv kuupäev. Eesmärk on automatiseerida defektide (vale toode, puuduv või vale silt) ja tootmisliini seisakute/sildivahetuste tuvastamine kaamerast saadava videopildi analüüsi abil. Oodatud kasu on vigade kiirem märkamine (võimaldab liini kiirelt seisma panna) ning statistika kogumine tootmisprotsessi efektiivsuse (seisakud, robotite jõudlus, materjali kulu) kohta.

### 🔴 1.2 Edukuse mõõdikud
Kuidas mõõdame rakenduse edukust? Mida peab rakendus teha suutma?

> Rakendus peab suutma edukalt eraldada videovoost vajaliku takti (kui liikumine peatub) hoolimata vahele segavatest faktoritest (näiteks töötajate käed või pead kaadris). Seejärel peab süsteem takti seest välja lõikama 4 toodet, tuvastama sildi olemasolu ning klassifitseerima, kas tegemist on õige tootega või mitte. Samuti peaks süsteem loendama tühje pakendeid ja logima iga takti väljundid hilisema statistika jaoks. Edukust mõõdetakse täpsuses – kui korrektselt eristatakse õigeid pille vigastest ning kas väljastatav statistika vastab kliendi reaalsele tootmistempo- ja veastatistikale.

### 🔴 1.3 Ressursid ja piirangud
Millised on ressursipiirangud (nt aeg, eelarve, tööjõud, arvutusvõimsus)? Millised on tehnilised ja juriidilised piirangud (GDPR, turvanõuded, platvorm)? Millised on piirangud tasuliste tehisintellekti mudelite kasutamisele?

> Lahendus peab toimima reaalajas või väga väikese viivitusega (tsükkel on ~7 sekundit). Tehniliseks piiranguks on see, et praegu on valede pakendite (anomaaliate) kohta andmebaas puudu, eksisteerivad peamiselt korrektsed andmed. Algselt keskendutakse ainult 4 erinevale tootele (reaalselt on neid liinil 30–40). Lisaks, tihti satuvad kaamera ette töötajate käed, seega analüüs algab vaid takti tuvastamisest. Vaja on jälgida 1 striimi (4 toodet). Turvaprobleeme andmetes seoses isikuandmetega üldiselt pole, kui kaadritesse ei jää otseselt nägusid (või neid ei analüüsita).

<br>
<br>


## 🟠 2. Andmete mõistmine
*Fookus: millised on meie andmed?*

### 🟠 2.1 Andmevajadus ja andmeallikad
Milliseid andmeid (ning kui palju) on lahenduse toimimiseks vaja? Kust andmed pärinevad ja kas on tagatud andmetele ligipääs?

> Andmeallikaks on tootmisliini kaamerast tulevad videostriimid. Hetkel on lahenduse arendamiseks kättesaadavad nelja (4) erineva toote 3-minutilised videolõigud. Tuleviku ja ajaloolise statistika osas on salvestatud videopilti umbes pool aastat, seega andmete puudust pikas plaanis ei ole.

### 🟠 2.2 Andmete kasutuspiirangud
Kas andmete kasutamine (sh ärilisel eesmärgil) on lubatud? Kas andmestik sisaldab tundlikku informatsiooni?

> Kuna andmed on tootmisettevõtte siseinfo (videod tootmisliinilt), on nende kasutamine piiratud konkreetse ettevõtte raamis. GDPR-i seisukohast ei sisalda andmed tundlikke isikuandmeid (välja arvatud juhuslikud töötajate kätekujutised, mis jäetakse analüüsist välja).

### 🟠 2.3 Andmete kvaliteet ja maht
Millises formaadis andmeid hoiustatakse? Mis on andmete maht ja andmestiku suurus? Kas andmete kvaliteet on piisav (struktureeritus, puhtus, andmete kogus) või on vaja märkimisväärset eeltööd)?

> Formaadi osas on tegemist videoandmetega. Maht on esialgu 4 lühikest (3 min) videot. Kvaliteet on varieeruv: piltidel on pidev liikumine, esinevad seisakud ja inimese käed kaadris. Märkimisväärne puudus on valede näidete andmebaasi puudumine – enamik andmeid kujutab korrektset toodet, mis teeb defektide otsimise puhtjuhuslikuks või nõuab anomaaliatuvastuse lähenemisi.

### 🟠 2.4 Andmete kirjeldamise vajadus
Milliseid samme on vaja teha, et kirjeldada olemasolevaid andmeid ja nende kvaliteeti.

> Vaja on luua ülevaade, kui sageli liin seiskub ja milline on visuaalne takistatus (käed kaadris). Tuleb analüüsida, kui hästi saab videost eraldada neljased pakendite grupid ning kui selged on triipkoodist/sildilt detailsed kirjed (toote nimi ja osaliselt ka salvestusaeg/säilivusaeg).

<br>
<br>


## 🟡 3. Andmete ettevalmistamine
Fookus: Toordokumentide viimine tehisintellekti jaoks sobivasse formaati.

### 🟡 3.1 Puhastamise strateegia
Milliseid samme on vaja teha andmete puhastamiseks ja standardiseerimiseks? Kui suur on ettevalmistusele kuluv aja- või rahaline ressurss?

> Esmane samm on videost kaadrite eraldamine – õige ajahetke (takti) tuvastamine. Loogika: kui liikumine peatub, oodatakse 2 sekundit kaamera fokuseerimiseks ja tehakse pilt. Valepiltide (kinnas ees, pidev muutumine käsitsi sildivahetusel) filtreerimiseks rakendatakse optilise voo (optical flow) analüüsi. Lõpuks lõigatakse igast kaadrist välja eraldi 4 toodet ja seejärel keskendutakse igal pildil pakendi keskossa.

### 🟡 3.2 Tehisintellektispetsiifiline ettevalmistus
Kuidas andmed tehisintellekti mudelile sobivaks tehakse (nt tükeldamine, vektoriseerimine, metaandmete lisamine)?

> Eraldatud üksikute toodete kujutised resaiditakse/normaliseeritakse tehisnägemise (computer vision) mudeli algsuurusele. Pildid peavad olema jaotatud klassidesse. Samuti on oluline tuvastatud triipkoodide või teksti optilise tekstituvastuse (OCR) jaoks sobivate pildiregioonide filtreerimine ja kontrastiparandused. Kuna valede toodete pilte ei ole, võib olla vajalik andmeid sünteesida või tekitada reeglipõhised anomaaliatuvastuse maskid.

<br>
<br>

## 🟢 4. Tehisintellekti rakendamine
Fookus: Tehisintellekti rakendamise süsteemi komponentide ja disaini kirjeldamine.

### 🟢 4.1 Komponentide valik ja koostöö
Millist tüüpi tehisintellekti komponente on vaja rakenduses kasutada? Kas on vaja ka komponente, mis ei sisalda tehisintellekti? Kas komponendid on eraldiseisvad või sõltuvad üksteisest (keerulisem agentsem disan)?

> Rakendus kasutab torujuhtme (pipeline) tüüpi disaini: 1) Klassikalise masinnägemise osa (ilma TI-ta) eraldab taktid ja lõikab välja tooted (nt optilise voo ja bounding box loogika). 2) Sildi ja toote õigsuse verifitseerija rakendab mudelit, mis klassifitseerib, kas toode vastab partii omale ning kas seal leidub aktiivselt silt. 3) Vajadusel tekstituvastus/triipkoodituvastus mudel partii alguses. Komponendid käituvad järjestikku iga liinil tehtud pildiga.

### 🟢 4.2 Tehisintellekti lahenduste valik
Milliseid mudeleid on plaanis kasutada? Kas kasutada valmis teenust (API) või arendada/majutada mudelid ise?

> Arvestades, et analüüs peab toimuma suure kiiruse ja mahuga (vaja pidevat monitooringut kohapeal), ei ole pilve-API-põhise teenuse (nt OpenAI Vision) kasutamine eelkõige latentsuse ja andmemahu/hinnakulu tõttu otstarbekas. Tehnoloogia poolest tuleks ehitada või peenhäälestada lokaalne kerge pildituvastusmudel (näiteks YOLO või ResNet baasil) lünkade/valede toodete tuvastamiseks ja avatud ressurssidega kaameratöötluse raamistik avatud OCR lahendusega. Mudelid tuleb majutada kliendi serverisse või tootmisliini juurde installeeritud seadmesse.

### 🟢 4.3 Kuidas hinnata rakenduse headust?
Kuidas rakenduse arenduse käigus hinnata rakenduse headust?

> Manuaalse seire ja prototüüpimise käigus. Videote alusel käiakse käsitsi üle, kas mudel märkas igat takti õigesti ja lükkas kõrvale pildid, kus on käed/takistused. Täpsuse mõõdikuks on vigade (valede toodete ja puuduvate siltide) tuvastamise % antud 3-minutilistes näidistes ja hiljem pikemas videosalvestises. Kuna anomaaliaid testandmetes esialgu napib, tuleb leida viis, kuidas simuleerida defekte mudeli täpsuse veendumiseks.

### 🟢 4.4 Rakenduse arendus
Milliste sammude abil on plaanis/on võimalik rakendust järk-järgult parandada (viibadisain, erinevte mudelite testimine jne)?

> Esimene etapp on usaldusväärse pildilõikus- ja taktiotsingusüsteemi väljaehitamine (andmete puhastus). Seejärel treenitakse mudel tuvastama praegust 4 toodet. Järgmise etapina seotakse triipkoodidelugemine partii kontrolliga. Edasine arendus kaasab uusi tooteiklassifikatsioone (kokku on tooteid 30-40) ehk mudeli ületreenimist või kohandamist (few-shot lähenemised uueteenuste kaasamisel) ja robustsuse kasvatamist (erinevad sildid ja valgusolud).

### 🟢 4.5 Riskijuhtimine
Kuidas maandatakse tehisintellektispetsiifilisi riske (hallutsinatsioonid, kallutatus, turvalisus)?

> Peamine risk on mudeli valepositiivsed tulemused – näiteks loetakse õige toode valeks valguse või kerge sildinihke tõttu, põhjustades asjatu liini seiskumise. Selle vastu lahendatakse süsteem pigem selliselt, et programm annab statistika reaalajas teada, aga klient otsustab (vähemalt alguses) ise seiskamise. Teine risk on "feilivad lugemised" takistuste (töötajate käed) tõttu. Seda leevendatakse sissehitatud reeglitega – näiteks kui kaadris leitakse sisseastuv anomaalia suuruses ja mustris (kinnas), eirab masin seda takti lihtsalt (ei loe seda veaks, mis vajaks häiret).

<br>
<br>

## 🔵 5. Tulemuste hindamine
Fookus: kuidas hinnata loodud lahenduse rakendatavust ettevõttes/probleemilahendusel?

### 🔵 5.1 Vastavus eesmärkidele
Kuidas hinnata, kas rakendus vastab seatud eesmärkidele?

> Lahendus annab väärtust, kui klient saab koostatavatest teavitatavatest raportitest logi statistika taktidest, sildivahetuste aegadest ja defektsetest pakenditest. Vastavust eesmärgile saab analüüsida selle põhjal, kas süsteem avastab eksperimentaalsetes proovisituatsioonides sihilikult rikutud partiid ja suudab raporteerida masinate tegelikku kiirust / tühjade pakendite arvu ning seisakuid vigadeta.

<br>
<br>

## 🟣 6. Juurutamine
Fookus: kuidas hinnata loodud lahenduse rakendatavust ettevõttes/probleemilahendusel?

### 🟣 6.1 Integratsioon
Kuidas ja millise liidese kaudu lõppkasutaja rakendust kasutab? Kuidas rakendus olemasolevasse töövoogu integreeritakse (juhul kui see on vajalik)?

> Süsteem väljastab reaalajas teavet tuvastatud taktide ja võimalike vigade ning tühjade pakendite kohta. Kuna klient teeb ise otsuse liini seiskumise osas (süsteem ei seisata automaatselt), peab lõpplahendus olema kasutajale nähtav kergesti ligipääsetaval monitooringuekraanil või logidesse suunatud armatuurlauana.

### 🟣 6.2 Rakenduse elutsükkel ja hooldus
Kes vastutab süsteemi tööshoidmise ja jooksvate kulude eest? Kuidas toimub rakenduse uuendamine tulevikus?

> Kuna mudel töötab praegu ainult 4 tootele, on elutsükli seisukohalt kindlustatud nõudlus mudeli uuendamiseks, et suuta klassifitseerida liinil olevaid kõiki 30-40 toodet ja toetada tootepakettide võimalikku disaini muutust või uusi etikette. Hoolduses on seega mudeli "retraining" korduv tegevus. Süsteem jookseb eeldatavasti kohalikus serveris, mistõttu vastutab installeerimise järgselt halduse ja serverikulude eest ilmselt tellija / ettevõtte IT.