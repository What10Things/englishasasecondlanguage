"""Original, finite editorial bank. Automation assembles resources, never invents facts."""
from .catalog import LANGUAGES

def rule(key, texts, questions):
    return {'id': key, 'explanations': dict(zip(('en','es','fr','pl'), texts)), 'questions': [
        {'id': f'{key}-{i+1}', 'prompt': prompt, 'options': options.split('|'), 'answer': answer}
        for i, (prompt, options, answer) in enumerate(questions)]}

BANK = {
'A1': [
rule('be', [
'Use am with I, is with he/she/it or one person, and are with you/we/they or more than one person.',
'Usa am con I, is con he/she/it o una persona, y are con you/we/they o varias personas.',
'Utilisez am avec I, is avec he/she/it ou une personne, et are avec you/we/they ou plusieurs personnes.',
'Używaj am z I, is z he/she/it lub jedną osobą, a are z you/we/they lub wieloma osobami.'
], [('I ___ a student.','am|is|are',0),('My sister ___ at home.','am|is|are',1),('Our neighbours ___ friendly.','is|am|are',2),('You ___ in the right room.','are|is|am',0)]),
rule('present', [
'In positive present simple sentences, add -s or -es with he/she/it. After does not, use the base form. I/you/we/they use the base form.',
'En frases afirmativas del presente simple, añade -s o -es con he/she/it. Después de does not, usa la forma base. I/you/we/they usan la forma base.',
'Au présent simple affirmatif, ajoutez -s ou -es avec he/she/it. Après does not, utilisez la base verbale. I/you/we/they prennent la base verbale.',
'W zdaniach twierdzących w present simple dodaj -s lub -es z he/she/it. Po does not użyj formy podstawowej. I/you/we/they łączą się z formą podstawową.'
], [('Leo ___ to work by bus.','go|goes|going',1),('We ___ dinner at seven.','eats|eating|eat',2),('She does not ___ meat.','eats|eat|eating',1),('My brother ___ English every day.','studies|study|studying',0)]),
rule('plural', [
'Use there is with one thing and there are with plural things. Use a before a singular countable noun beginning with a consonant sound, and an before a vowel sound.',
'Usa there is con una cosa y there are con varias. Usa a antes de un sustantivo contable singular que empieza por sonido consonántico y an antes de sonido vocálico.',
'Utilisez there is au singulier et there are au pluriel. Employez a devant un nom dénombrable singulier commençant par un son consonantique, et an devant un son vocalique.',
'Używaj there is przy jednej rzeczy, a there are przy liczbie mnogiej. Przed rzeczownikiem policzalnym w liczbie pojedynczej użyj a przed dźwiękiem spółgłoski, a an przed dźwiękiem samogłoski.'
], [('There ___ a book on the desk.','are|is|be',1),('There ___ three windows.','is|am|are',2),('I have ___ umbrella.','a|an|two',1),('This is ___ useful map.','a|an|three',0)])],
'A2': [
rule('past', [
'Use the past simple for completed events at a finished time. Went and bought are irregular past forms. After did or did not, use the base form.',
'Usa el pasado simple para hechos terminados en un tiempo acabado. Went y bought son formas irregulares. Después de did o did not, usa la forma base.',
'Utilisez le prétérit pour un événement terminé à un moment révolu. Went et bought sont irréguliers. Après did ou did not, utilisez la base verbale.',
'Używaj past simple do zakończonych zdarzeń w zakończonym czasie. Went i bought to formy nieregularne. Po did lub did not użyj formy podstawowej.'
], [('Yesterday we ___ to the park.','go|went|gone',1),('She ___ a ticket last night.','buy|bought|buying',1),('Did you ___ the film yesterday?','saw|seen|see',2),('He did not ___ the door.','open|opened|opening',0)]),
rule('comparison', [
'Use a comparative to compare two things: short adjectives usually take -er; longer adjectives usually take more. Good becomes better. Do not combine more and an -er comparative.',
'Usa el comparativo para comparar dos cosas: los adjetivos cortos suelen llevar -er y los largos more. Good se convierte en better. No combines more con un comparativo en -er.',
'Pour comparer deux choses, les adjectifs courts prennent généralement -er et les longs more. Good devient better. Ne combinez pas more avec un comparatif en -er.',
'Do porównania dwóch rzeczy użyj stopnia wyższego: krótkie przymiotniki zwykle przyjmują -er, a dłuższe more. Good zmienia się w better. Nie łącz more ze stopniem wyższym na -er.'
], [('This room is ___ than mine.','small|smaller|smallest',1),('The train is ___ expensive than the bus.','more|most|much',0),('This answer is ___ than my first one.','good|best|better',2),('Today is ___ than yesterday.','colder|more colder|coldest',0)]),
rule('plans', [
'Use am/is/are going to + base verb for a plan. Much goes with uncountable nouns such as water; many goes with plural countable nouns such as bags.',
'Usa am/is/are going to + verbo base para un plan. Much acompaña a incontables como water; many a contables plurales como bags.',
'Utilisez am/is/are going to + base verbale pour un projet. Much accompagne les indénombrables comme water ; many les noms dénombrables pluriels comme bags.',
'Dla planu użyj am/is/are going to + forma podstawowa. Much łączy się z niepoliczalnymi, np. water, a many z policzalnymi w liczbie mnogiej, np. bags.'
], [('I am going ___ my aunt tomorrow.','visit|to visit|visiting',1),('They ___ going to cook tonight.','is|am|are',2),('How ___ water is in the bottle?','many|much|few',1),('How ___ bags do you need?','many|much|little',0)])],
'B1': [
rule('perfect', [
'Use the present perfect (have/has + past participle) for a situation continuing until now or an experience without a finished past time. Since marks a starting point; for marks a duration.',
'Usa el presente perfecto (have/has + participio) para situaciones que continúan hasta ahora o experiencias sin tiempo pasado acabado. Since señala el inicio y for la duración.',
'Utilisez le present perfect (have/has + participe passé) pour une situation qui dure encore ou une expérience sans date passée révolue. Since marque le début ; for la durée.',
'Używaj present perfect (have/has + imiesłów) do sytuacji trwającej do teraz lub doświadczenia bez zakończonego czasu przeszłego. Since wskazuje początek, for okres trwania.'
], [('I have worked here ___ 2021.','for|since|during',1),('She has lived here ___ three years.','since|from|for',2),('Have you ever ___ a horse?','rode|ridden|ride',1),('He ___ already finished his homework.','has|have|did',0)]),
rule('conditional', [
'For a real future possibility, use if + present simple and will + base verb. After a modal such as should, use the base verb without to.',
'Para una posibilidad futura real, usa if + presente simple y will + verbo base. Después de un modal como should, usa el verbo base sin to.',
'Pour une possibilité future réelle, utilisez if + présent simple et will + base verbale. Après un modal comme should, employez la base verbale sans to.',
'Dla realnej przyszłej możliwości użyj if + present simple oraz will + forma podstawowa. Po czasowniku modalnym, np. should, użyj formy podstawowej bez to.'
], [('If it rains, we ___ indoors.','will stay|stayed|would stay',0),('If she ___ now, she will catch the bus.','will leave|leaves|left',1),('You should ___ a break.','to take|taking|take',2),('If I see him, I ___ him your message.','gave|give yesterday|will give',2)]),
rule('relative', [
'Who refers to a person; whose shows possession; where refers to a place. After enjoy, use the -ing form of a verb.',
'Who se refiere a una persona; whose indica posesión; where se refiere a un lugar. Después de enjoy, usa la forma en -ing.',
'Who désigne une personne ; whose exprime la possession ; where désigne un lieu. Après enjoy, utilisez la forme en -ing.',
'Who odnosi się do osoby, whose oznacza posiadanie, a where odnosi się do miejsca. Po enjoy użyj formy z -ing.'
], [('That is the teacher ___ helped me.','which|who|where',1),('This is the student ___ bag was lost.','who|where|whose',2),('This is the café ___ we first met.','where|whose|who',0),('I enjoy ___ in the sea.','swim|swimming|to swim',1)])],
'B2': [
rule('passive', [
'The passive uses be + past participle. Choose the tense of be to match the time. The past perfect passive uses had been + past participle for an earlier past action.',
'La pasiva usa be + participio. Elige el tiempo de be según el momento. El pasado perfecto pasivo usa had been + participio para una acción anterior a otra pasada.',
'Le passif se construit avec be + participe passé. Adaptez le temps de be au contexte. Le past perfect passif emploie had been + participe passé pour une action antérieure à une autre action passée.',
'Strona bierna ma postać be + imiesłów. Dopasuj czas be do sytuacji. Past perfect passive to had been + imiesłów dla czynności wcześniejszej od innej przeszłej.'
], [('The bridge ___ in 1998.','was built|is building|has build',0),('The applications ___ every Friday.','review|are reviewed|is reviewed',1),('By the time we arrived, the room ___.','has cleaned|had been cleaned|is cleaning',1),('The results will ___ tomorrow.','announce|announced|be announced',2)]),
rule('unreal', [
'For an unreal present situation, use if + past simple and would + base verb. For an unreal past situation, use if + past perfect and would have + past participle.',
'Para una situación presente irreal, usa if + pasado simple y would + verbo base. Para una situación pasada irreal, usa if + pasado perfecto y would have + participio.',
'Pour une situation présente irréelle, utilisez if + prétérit et would + base verbale. Pour une situation passée irréelle, utilisez if + past perfect et would have + participe passé.',
'Dla nierealnej sytuacji teraźniejszej użyj if + past simple i would + forma podstawowa. Dla nierealnej sytuacji przeszłej użyj if + past perfect i would have + imiesłów.'
], [('If I had more time, I ___ another language.','will learn|would learn|had learned',1),('If she ___ earlier, she would have caught the train.','leaves|would leave|had left',2),('If we had checked the map, we ___ lost.','would not have got|will not get|did not get',0),('If he ___ the answer, he would tell us.','knows|knew|will know',1)]),
rule('deduction', [
'For past deduction, use must have + past participle for a strong positive inference and cannot have for impossibility. In past reported speech, will usually becomes would and am/is becomes was.',
'Para deducir sobre el pasado, usa must have + participio para una inferencia afirmativa fuerte y cannot have para imposibilidad. En estilo indirecto pasado, will suele pasar a would y am/is a was.',
'Pour une déduction passée, utilisez must have + participe passé pour une forte probabilité et cannot have pour une impossibilité. Au discours indirect passé, will devient généralement would et am/is devient was.',
'Dla wnioskowania o przeszłości użyj must have + imiesłów dla silnego przekonania, a cannot have dla niemożliwości. W mowie zależnej w przeszłości will zwykle zmienia się w would, a am/is w was.'
], [('The ground is wet. It must ___ during the night.','rain|have rained|raining',1),('She was abroad all week, so she cannot ___ at yesterday’s meeting.','be|being|have been',2),('He said he ___ call the next day.','would|will to|can to',0),('She said that she ___ tired at that moment.','is being|was|will be',1)])],
'C1': [
rule('inversion', [
'After a fronted negative or restrictive expression such as never, rarely, not until or only then, invert the auxiliary and subject in the main clause. Use did + base verb when there is no other auxiliary in the past simple.',
'Tras una expresión negativa o restrictiva inicial como never, rarely, not until u only then, invierte auxiliar y sujeto en la oración principal. Usa did + verbo base si no hay otro auxiliar en pasado simple.',
'Après une expression négative ou restrictive en tête comme never, rarely, not until ou only then, inversez auxiliaire et sujet dans la principale. Utilisez did + base verbale si le prétérit n’a pas d’autre auxiliaire.',
'Po wyrażeniu przeczącym lub ograniczającym na początku, np. never, rarely, not until lub only then, odwróć kolejność operatora i podmiotu w zdaniu głównym. W past simple bez innego operatora użyj did + forma podstawowa.'
], [('Rarely ___ such a clear explanation.','I have heard|have I heard|heard I have',1),('Only then ___ the problem.','did I understand|I understood|did I understood',0),('Never ___ so relieved before.','she had felt|felt she had|had she felt',2),('Not until Monday ___ the news.','we heard|did we hear|did we heard',1)]),
rule('focus', [
'A what-cleft uses a clause beginning with what as a subject, usually followed by is or was. In an it-cleft, it is/was highlights the focused element, followed by a that-clause. After a preposition, use a noun or an -ing form.',
'Una oración hendida con what usa una cláusula con what como sujeto, normalmente seguida de is o was. En una hendida con it, it is/was destaca el elemento, seguido de una cláusula con that. Tras una preposición, usa sustantivo o forma en -ing.',
'Une phrase clivée en what prend une proposition en what comme sujet, généralement suivie de is ou was. Une clivée en it utilise it is/was pour mettre un élément en relief, suivi de that. Après une préposition, utilisez un nom ou une forme en -ing.',
'Konstrukcja z what ma zdanie z what jako podmiot, zwykle z is lub was. Konstrukcja z it is/was wyróżnia element, po którym następuje zdanie z that. Po przyimku użyj rzeczownika lub formy z -ing.'
], [('What matters most ___ the quality of the evidence.','are|is|have',1),('It was the timing ___ caused the problem.','what|whose|that',2),('The committee objected to ___ the deadline.','extend|extending|extended',1),('What surprised me ___ his calm response.','was|were|have',0)]),
rule('concession', [
'Although and even though introduce clauses with a subject and verb. Despite and in spite of introduce a noun or -ing phrase. Had + subject + past participle can replace if + past perfect in formal conditions.',
'Although y even though introducen oraciones con sujeto y verbo. Despite e in spite of introducen un sustantivo o frase en -ing. Had + sujeto + participio puede sustituir a if + pasado perfecto en condiciones formales.',
'Although et even though introduisent une proposition avec sujet et verbe. Despite et in spite of précèdent un nom ou un groupe en -ing. Had + sujet + participe passé peut remplacer if + past perfect dans une condition formelle.',
'Although i even though wprowadzają zdanie z podmiotem i czasownikiem. Despite i in spite of wprowadzają rzeczownik lub wyrażenie z -ing. Had + podmiot + imiesłów może zastąpić if + past perfect w warunkach formalnych.'
], [('___ the evidence was limited, the team continued.','Despite|Although|In spite of',1),('___ facing delays, they completed the work.','Although|Even though|Despite',2),('Had we known earlier, we ___ differently.','would have acted|will act|act',0),('In spite of ___ tired, she finished the report.','be|being|was',1)])],
'C2': [
rule('nuance', [
'Choose the word that matches the precise meaning and collocation: equivocal means ambiguous; tacit means understood without being stated; tenuous means weak or slight; cogent describes clear, convincing reasoning.',
'Elige la palabra según el significado preciso y la combinación: equivocal significa ambiguo; tacit, implícito; tenuous, débil o tenue; cogent describe un razonamiento claro y convincente.',
'Choisissez selon le sens précis et l’association de mots : equivocal signifie ambigu ; tacit, compris sans être exprimé ; tenuous, fragile ; cogent qualifie un raisonnement clair et convaincant.',
'Dobierz słowo do znaczenia i połączenia: equivocal oznacza niejednoznaczny; tacit — rozumiany bez wyrażenia słowami; tenuous — słaby lub nikły; cogent opisuje jasne i przekonujące rozumowanie.'
], [('The reply was deliberately ___, leaving both interpretations open.','equivocal|unequivocal|explicit',0),('Their silence was taken as ___ approval, though nobody said yes.','vocal|tacit|outspoken',1),('The link was so ___ that the conclusion could not be justified.','irrefutable|conclusive|tenuous',2),('Her argument was ___: every conclusion followed clearly from the evidence.','cogent|incoherent|evasive',0)]),
rule('collocation', [
'Fixed combinations matter: bear in mind means remember; call into question means cast doubt on; draw a distinction means identify a difference; tally with means agree with or match.',
'Las combinaciones fijas importan: bear in mind significa tener presente; call into question, poner en duda; draw a distinction, establecer una diferencia; tally with, coincidir con.',
'Les associations fixes sont essentielles : bear in mind signifie garder à l’esprit ; call into question, remettre en question ; draw a distinction, établir une différence ; tally with, correspondre à.',
'Ważne są stałe połączenia: bear in mind oznacza pamiętać o; call into question — podawać w wątpliwość; draw a distinction — wprowadzać rozróżnienie; tally with — zgadzać się z.'
], [('We should ___ in mind that the sample was small.','carry|bear|hold',1),('The discovery calls the original conclusion ___ question.','into|onto|over',0),('It is important to ___ a distinction between correlation and causation.','do|make up|draw',2),('Her account does not ___ with the available evidence.','tally|corroborate|substantiate',0)]),
rule('rhetoric', [
'Formal concession and purpose use precise patterns: be that as it may acknowledges a point before disagreeing; with a view to takes an -ing form; lest can introduce should + base verb; so + adjective at the start can trigger inversion.',
'La concesión y finalidad formales siguen patrones precisos: be that as it may admite un punto antes de discrepar; with a view to lleva -ing; lest puede introducir should + verbo base; so + adjetivo inicial puede provocar inversión.',
'La concession et le but formels suivent des constructions précises : be that as it may admet un point avant une objection ; with a view to prend -ing ; lest peut introduire should + base verbale ; so + adjectif en tête peut entraîner une inversion.',
'Formalne ustępstwo i cel mają ścisłe konstrukcje: be that as it may uznaje argument przed zastrzeżeniem; with a view to wymaga -ing; lest może wprowadzać should + formę podstawową; początkowe so + przymiotnik może wywołać inwersję.'
], [('Be that as it ___, the central objection remains.','can|may|would',1),('They revised the policy with a view to ___ waste.','reduce|reduced|reducing',2),('She recorded every change lest any detail ___ overlooked.','should be|has being|would been',0),('So compelling ___ that the panel changed its decision.','the evidence was|was the evidence|did the evidence',1)])]
}
# English production tasks deliberately stay in the target language.
TASKS = {
'A1': ['Write four sentences introducing yourself and a friend. Use am, is and are.', 'Describe your room in four sentences. Use there is, there are, a and an.'],
'A2': ['Write 60–80 words about a day trip you took. Include three past simple verbs.', 'Compare two places you know, then describe a plan to visit one. Write 60–80 words.'],
'B1': ['Write 100–120 words about a skill you have learned. Use for, since and a relative clause.', 'Write an email giving a friend advice about a trip. Include two first conditional sentences.'],
'B2': ['Write 140–180 words about a decision you regret. Include two third conditional sentences.', 'Write a short report about a change in your town. Include passive forms and clearly separate facts from deductions.'],
'C1': ['Write 180–220 words evaluating a proposal to shorten the working week. Use concession and one natural example of inversion.', 'Rewrite a message requesting a deadline extension for a formal audience, then for a close colleague. Explain your register choices.'],
'C2': ['Write 220–260 words distinguishing a plausible claim from a compelling argument. Use precise collocations and qualify uncertain claims.', 'Write two 120-word accounts of the same fictional meeting: one neutral and one subtly ironic. Annotate three choices that change the tone.']}

def questions_for(level):
    return [dict(q, explanations=r['explanations'], rule=r['id']) for r in BANK[level] for q in r['questions']]

def validate_bank():
    ids = set()
    for level, rules in BANK.items():
        assert len(rules) == 3
        for r in rules:
            assert set(r['explanations']) == set(LANGUAGES)
            assert all(len(x) > 30 for x in r['explanations'].values())
            for q in r['questions']:
                assert q['id'] not in ids
                ids.add(q['id'])
                assert q['prompt'].count('___') == 1
                assert len(set(q['options'])) == 3
                assert 0 <= q['answer'] < len(q['options'])
    return len(ids)

# Extend every authored rule, with no silent English fallback.
import json
from pathlib import Path
from .catalog import NEW_LANGUAGES
for code in NEW_LANGUAGES:
    translations = json.loads((Path(__file__).parent / 'locales' / f'{code}-rules.json').read_text(encoding='utf-8'))
    ids = {r['id'] for rules in BANK.values() for r in rules}
    if set(translations) != ids or not all(translations.values()):
        raise ValueError(f'Incomplete answer explanations for {code}')
    for rules in BANK.values():
        for r in rules:
            r['explanations'][code] = translations[r['id']]
