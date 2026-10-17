#!/usr/bin/env python3
"""Génère le site de démonstration examples/demo-site/project.mobirise (11 pages + une page « tous les blocs »).

Le point de départ est un projet Mobirise réel contenant au moins une instance de chaque bloc
(examples/base.mobirise) : les composants en sont clonés tels que Mobirise les a enregistrés, seuls
le texte, les liens et les options sont modifiés. Le contenu est fictif et générique.

Usage : python3 -I tools/build_demo.py [--base examples/base.mobirise] [--out examples/demo-site/project.mobirise]
"""
import argparse
import copy
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skyline as sk  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--base", default=os.path.join(sk.ROOT, "examples", "base.mobirise"))
ap.add_argument("--out", default=os.path.join(sk.ROOT, "examples", "demo-site", "project.mobirise"))
args = ap.parse_args()

ALL = "ALL"  # remplace toutes les occurrences au lieu de la première


# ---------------------------------------------------------------- édition du HTML d'un bloc

def split_block(html):
    """(en-tête jusqu'à </mbr-parameters>, corps, <style> final) : on n'édite le texte que dans le corps."""
    i = html.index("</mbr-parameters>") + len("</mbr-parameters>")
    j = html.rfind("<style>")
    return html[:i], html[i:j], html[j:]


def edit(html, pairs):
    head, body, tail = split_block(html)
    for pair in pairs:
        old, new = pair[0], pair[1]
        if old not in body:
            raise SystemExit("Texte introuvable dans le bloc : %r" % old)
        body = body.replace(old, new) if len(pair) > 2 and pair[2] == ALL else body.replace(old, new, 1)
    return head + body + tail


def sequence(html, old, news):
    """Remplace successivement les N premières occurrences de `old` par `news[0]`, `news[1]`, ..."""
    return edit(html, [(old, n) for n in news])


def hrefs(html, links):
    """Remplace les N premiers attributs href du corps (None = inchangé)."""
    head, body, tail = split_block(html)
    it = iter(links)
    body = re.sub(r'href="[^"]*"', lambda m: m.group(0) if (n := next(it, None)) is None else 'href="%s"' % n, body)
    return head + body + tail


def param(html, name, value):
    """Change la valeur par défaut d'une option, comme le fait Mobirise dans <mbr-parameters>."""
    head, body, tail = split_block(html)
    m = re.search(r'<select[^>]*\bname="%s"[^>]*>.*?</select>' % re.escape(name), head, re.S)
    if m:
        sel = re.sub(r'\s+selected(="")?', "", m.group(0))
        sel = re.sub(r'(<option value="%s")' % re.escape(str(value)), r'\1 selected=""', sel, count=1)
        head = head.replace(m.group(0), sel)
        return head + body + tail
    m = re.search(r'<input[^>]*\bname="%s"[^>]*>' % re.escape(name), head)
    if not m:
        raise SystemExit("Option introuvable : " + name)
    tag = m.group(0)
    if 'type="checkbox"' in tag:
        new = re.sub(r"\s+checked(=\"\")?", "", tag)
        if value:
            new = new[:-1] + ' checked="">'
    else:
        new = re.sub(r'value="[^"]*"', 'value="%s"' % value, tag)
    return head.replace(tag, new) + body + tail


# ---------------------------------------------------------------- composants

base = json.load(open(args.base, encoding="utf-8"))
settings = base["settings"]
protos = {}
for page in base["pages"].values():
    for c in page["components"]:
        protos.setdefault(c["_name"], c)

_counter = [settings["uniqCompNum"]]


def b36(n):
    s = ""
    while n:
        n, r = divmod(n, 36)
        s = "0123456789abcdefghijklmnopqrstuvwxyz"[r] + s
    return s or "0"


def cid(*parts):
    h = int(hashlib.sha1("|".join(parts).encode()).hexdigest(), 16)
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    out = ""
    for _ in range(10):
        h, r = divmod(h, len(chars))
        out += chars[r]
    return out


BOOLEAN_ATTRS = r"checked|inline|selected|parallax|global|once|hidden|required|action|mbr-list|mbr-text|mbr-buttons|mbr-form|mbr-icon"


def prototype(key):
    """Composant construit depuis les sources actuelles (les valeurs, `_styles` et CSS du projet de base peuvent être périmés).
    Seule la forme du composant (alias, thème source...) est reprise du projet de base, comme Mobirise l'a enregistrée."""
    for g, p in sk.block_files():
        b = sk.load_block(g, p)
        if b["key"] != key:
            continue
        html = sk.native_html(b)
        html = re.sub(r"<[^>]+>", lambda m: re.sub(r"\s(%s)(?=[\s>])" % BOOLEAN_ATTRS, r' \1=""', m.group(0)), html)
        root = re.search(r"<section[^>]*>", html).group(0)
        c = copy.deepcopy(protos.get(key, {"alias": "skyline-blocks/components", "_isSecondary": True, "_sourceTheme": "startm5",
                                           "_protectedParams": [], "_params": {}}))
        c.update({"_name": key, "_customHTML": html, "_styles": b["styles"], "_global": " global" in root, "_once": " once" in root})
        return c
    raise SystemExit("Bloc inconnu : " + key)


def comp(page, index, key, edits=(), params=None, links=None, seqs=()):
    c = prototype(key)
    html = c["_customHTML"]
    for name, value in (params or {}).items():
        html = param(html, name, value)
    html = edit(html, edits)
    for old, news in seqs:
        html = sequence(html, old, news)
    if links:
        html = hrefs(html, links)
    i = html.rfind("<style>")  # CSS embarqué : toujours régénéré depuis theme/skyline.css (celui du projet de base peut être ancien)
    c["_customHTML"] = html[:i] + "<style>%s</style>" % sk.css_for(html) + html[html.index("</style>", i) + len("</style>"):]
    c["_cid"] = cid("global", key) if c["_global"] else cid(page, key, str(index))  # blocs globaux : même _cid sur toutes les pages
    c["_anchor"] = "%s-%s" % (key, b36(_counter[0]))
    _counter[0] += 1
    return c


# ---------------------------------------------------------------- contenu (fictif, générique)

PAGES = {  # fichier -> (titre, description)
    "index.html": ("Accueil", "Festival Horizon : quatre jours de rencontres, d'ateliers et de spectacles."),
    "about.html": ("À propos", "Qui sommes-nous, le lieu et nos équipes."),
    "programme.html": ("Programme", "Les horaires des deux jours d'animations."),
    "tickets.html": ("Billets", "Billets, chambres, niveaux de soutien et goodies."),
    "faq.html": ("FAQ", "Les questions fréquentes."),
    "register.html": ("S'inscrire", "Les étapes de l'inscription et le formulaire de demande."),
    "join-us.html": ("Recrutement", "Les postes de bénévoles à pourvoir."),
    "contact.html": ("Contact", "Écrivez-nous et trouvez le lieu."),
    "rules.html": ("Règlement", "Le règlement de l'événement."),
    "vendor-rules.html": ("Règlement des exposants", "Conditions applicables aux exposants."),
    "legal.html": ("Mentions légales", "Mentions légales."),
    "all-blocks.html": ("Tous les blocs", "Chaque bloc Skyline une fois, avec son contenu par défaut."),
}

TITLE_CTA = "Ready to take off?"


def menu(page, i):
    return comp(page, i, "sk-menu1", [
        (">Brand<", ">Horizon<"), (">Home<", ">Accueil<"), (">About<", ">À propos<"),
        (">Tickets<", ">Billets<"), (">Register<", ">S'inscrire<")],
        links=["index.html", "index.html", "about.html", "programme.html", "tickets.html", "faq.html", "register.html"])


def footer(page, i):
    return comp(page, i, "sk-footer2", [
        ("Join us! #2027", "Rejoignez-nous ! #HORIZON27"), ("Your Event Name", "Festival Horizon"),
        (">About us<", ">À propos<"), (">Recruitment<", ">Recrutement<"), (">Rules<", ">Règlement<"),
        (">Vendor rules<", ">Règlement des exposants<"), (">Legal notice<", ">Mentions légales<")],
        links=["about.html", "join-us.html", "contact.html", "rules.html", "vendor-rules.html", "legal.html"])


def text(page, i, title, para, signature=None):
    edits = [("Welcome aboard", title),
             ("Introduce your event or organisation in two or three paragraphs. Keep the tone friendly and invite visitors to read on. Replace this placeholder with your own text.", para)]
    if signature:
        edits.append(("The team is waiting for you!", signature))
    return comp(page, i, "sk-text1", edits, params=None if signature else {"showSignature": False})


def cta(page, i, title, para, b1, l1, b2, l2):
    return comp(page, i, "sk-cta1", [(TITLE_CTA, title), ("A short sentence that invites people to act now.", para),
                                     ("Get your pass", b1), ("Learn more", b2)], links=[l1, l2])


def notice(page, i, title, para, style=None):
    return comp(page, i, "sk-notice1", [("Please note", title), ("Use this banner for conditions, deadlines or important reminders.", para)],
                params={"noticeStyle": style} if style else None)


def venue(page, i, title, para, side="right"):
    return comp(page, i, "sk-venue1", [
        ("The venue", title),
        ("Describe the venue: its size, its facilities, what makes it a good fit. One short paragraph is enough.", para),
        ("123 Example Avenue", "12 avenue de la Plage"), ("75000 City", "00000 Rivage-sur-Mer"),
        (">Metro:<", ">Tram :<"), ("lines 1 and 2", "ligne T2"), (">Train:<", ">Train :<"), ("lines A and B", "gare de Rivage-sur-Mer"),
        (">Bus:<", ">Bus :<"), ("12 and N34", "lignes 12 et N34"), (">Car:<", ">Voiture :<"), ("motorway exit 5", "autoroute, sortie 5")],
        params={"imageSide": side})


def teams(page, i, count, names):
    old = ["ACCOUNTING", "SAFETY", "STAGE", "TECHNOLOGY", "LOGISTICS", "COMMUNICATION"]
    edits = [("Our teams", "Nos équipes"), ("Who does what.", "Qui fait quoi."),
             ("One short paragraph describing what this team does and why it matters.", "Un court paragraphe qui décrit le rôle de cette équipe et son importance.", ALL)]
    edits += [(">%s<" % o, ">%s<" % n) for o, n in zip(old, names)]
    return comp(page, i, "sk-departments1", edits, params={"deptCount": count})


def faq(page, i, title, qa):
    olds = ["Where does the event take place?", "Can I get a refund?", "Is there an age limit?", "How do I contact the team?", "Question five?", "Question six?"]
    shown = len(qa)
    qa = list(qa) + [("Question supplémentaire ?", "Réponse à compléter.")] * (6 - shown)  # éléments masqués : pas de texte anglais résiduel
    edits = [("Frequently asked questions", title)] + [(o, q) for o, (q, _) in zip(olds, qa)]
    return comp(page, i, "sk-faq1", edits, params={"questions": shown},
                seqs=[("Write a clear answer here, in one or two short paragraphs.", [a for _, a in qa])])


def table(page, i, title, sub, cols, rows, note, prices):
    edits = [("Room rates", title), ("Price per person, per night.", sub), ("Room type", cols[0]), ("1 person", cols[1]), ("2 people", cols[2]), ("3 people", cols[3]),
             ("Standard room", rows[0]), ("Comfort room", rows[1]),
             ("Please note: prices include taxes and breakfast. Sharing conditions apply.", note)]
    edits += [("€ %s" % p, "%s €" % p, ALL) for p in prices]
    return comp(page, i, "sk-table1", edits)


def form(page, i, title, sub, thanks, phone=False):
    return comp(page, i, "sk-form1", [("Contact us", title), ("We usually reply within two days.", sub), ("Thanks for filling out the form!", thanks),
                                      (">Name<", ">Nom<"), (">Email<", ">E-mail<"), (">Phone<", ">Téléphone<"), (">Send<", ">Envoyer<")],
                params={"showPhone": phone})


def steps(page, i, title, count):
    return comp(page, i, "sk-steps1", [
        ("How it works", title),
        ("Create your account", "Créez votre compte"), ("Describe the first step in one or two sentences.", "Renseignez vos informations en quelques minutes."),
        ("Choose your ticket", "Choisissez votre billet"), ("Describe the second step in one or two sentences.", "Sélectionnez la formule qui vous convient."),
        ("Pay and confirm", "Payez et confirmez"), ("Describe the third step in one or two sentences.", "Réglez en ligne et recevez votre confirmation par e-mail."),
        ("Enjoy the event", "Profitez du festival"), ("Describe the fourth step in one or two sentences.", "Présentez votre billet à l'entrée et laissez-vous embarquer.")],
        params={"stepsAmount": count})


def build_pages():
    pages = {}

    p = "index.html"
    pages[p] = [
        menu(p, 0),
        comp(p, 1, "sk-hero1", [("12 – 15 June 2027", "12 – 15 juin 2027"), ("Seaside Congress Center", "Centre des Congrès Rivage"), ("Your Event Name", "Festival Horizon"),
                                ("A bold, friendly header with a title, a short pitch and clear calls to action. Replace this text with your own.",
                                 "Quatre jours de rencontres, d'ateliers et de spectacles au bord de la mer. Embarquez avec nous !"),
                                ("Get your pass", "Réserver mon billet"), ("See the programme", "Voir le programme")],
             links=["tickets.html", "programme.html"]),
        text(p, 2, "Bienvenue à bord", "Le Festival Horizon réunit chaque année des passionnés de toute la France pour quatre jours de rencontres, d'ateliers et de spectacles. Que vous veniez seul, entre amis ou en famille, il y a une place pour vous à bord.", "L'équipe Horizon vous attend !"),
        comp(p, 3, "sk-cards1", [("Why join us", "Pourquoi venir ?"), ("Three reasons, one short sentence each.", "Trois bonnes raisons de réserver dès maintenant."),
                                 ("Feature one", "Rencontres"), ("Short description of the first feature. Keep it to two lines.", "Retrouvez la communauté et faites de nouvelles rencontres dans un cadre convivial."),
                                 ("Feature two", "Ateliers"), ("Short description of the second feature. Keep it to two lines.", "Initiez-vous, créez et partagez vos talents avec des animateurs passionnés."),
                                 ("Feature three", "Spectacles"), ("Short description of the third feature. Keep it to two lines.", "Concerts, défilés et soirées pour finir chaque journée en beauté.")]),
        steps(p, 4, "Comment s'inscrire ?", 3),
        cta(p, 5, "Prêt au décollage ?", "Les places partent vite : réservez votre billet dès aujourd'hui.", "Réserver mon billet", "tickets.html", "En savoir plus", "about.html"),
        comp(p, 6, "sk-gallery1", [("Memories from last time", "Souvenirs de la dernière édition"), ("A look back at the previous edition.", "Un petit retour en images sur l'édition précédente.")]),
        footer(p, 7)]

    p = "about.html"
    pages[p] = [
        menu(p, 0),
        text(p, 1, "Qui sommes-nous ?", "Le Festival Horizon est organisé par une équipe de bénévoles passionnés. Depuis plusieurs éditions, nous faisons vivre un événement chaleureux, ouvert à toutes et à tous, où chacun peut partager ses passions.", "Rejoignez-nous : #HORIZON27"),
        venue(p, 2, "Le lieu", "Le Centre des Congrès Rivage accueille le festival : 10 000 m² d'espaces modulables, des salles de spectacle, un restaurant et une terrasse face à la mer."),
        teams(p, 3, 4, ["ACCUEIL", "SÉCURITÉ", "SCÈNE", "TECHNIQUE", "LOGISTIQUE", "COMMUNICATION"]),
        cta(p, 4, "Envie de nous rejoindre ?", "Rejoignez l'équipe de bénévoles ou venez simplement profiter du festival.", "Recrutement", "join-us.html", "Réserver mon billet", "tickets.html"),
        footer(p, 5)]

    p = "programme.html"
    pages[p] = [
        menu(p, 0),
        text(p, 1, "Programme", "Retrouvez ici les temps forts du festival. Les horaires peuvent évoluer : pensez à consulter cette page avant votre venue."),
        comp(p, 2, "sk-schedule1", [
            ("Programme", "Horaires"), ("Two days of activities.", "Deux jours d'animations."), (">Friday<", ">Vendredi<"), (">Saturday<", ">Samedi<"),
            ("Opening ceremony", "Cérémonie d'ouverture"), ("Panel: getting started", "Table ronde : bien débuter"), ('sk-event-name">Workshop<', 'sk-event-name">Atelier créatif<'),
            ("Morning session", "Session du matin"), (">Parade<", ">Défilé<"), (">Party<", ">Soirée<"),
            (">Main<", ">Scène<", ALL), (">Panel<", ">Conférence<"), (">Workshop<", ">Atelier<"), (">Event<", ">Animation<"), (">Dance<", ">Danse<")]),
        notice(p, 3, "À noter", "Le programme est susceptible d'évoluer. Les horaires définitifs seront confirmés à l'ouverture des portes."),
        cta(p, 4, "Pas encore de billet ?", "Réservez votre place pour ne rien manquer.", "Réserver mon billet", "tickets.html", "Poser une question", "faq.html"),
        footer(p, 5)]

    p = "tickets.html"
    pages[p] = [
        menu(p, 0),
        comp(p, 1, "sk-pricing1", [
            (">Tickets<", ">Billets<"), ("Pick the plan that suits you.", "Choisissez la formule qui vous convient."),
            ("Everything in Standard", "Tout le pass Standard"), ("Everything in Plus", "Tout le pass Plus"),
            (">Standard<", ">Pass Standard<"), (">Plus<", ">Pass Plus<"), (">Premium<", ">Pass Premium<"),
            ("€ 50", "50 €"), ("€ 90", "90 €"), ("€ 150", "150 €"),
            ("Entry to all days", "Accès aux quatre jours"), ("Welcome pack", "Pack de bienvenue"), ("Access to the schedule", "Accès au programme complet"),
            (">Choose<", ">Choisir<", ALL), ("Most popular", "Le plus choisi"), ("Priority entry", "Entrée prioritaire"), ("Exclusive gift", "Cadeau exclusif"),
            ("Reserved seating", "Places réservées"), ("Meet &amp; greet", "Rencontre avec les invités")],
            links=["register.html", "register.html", "register.html"]),
        table(p, 2, "Tarifs des chambres", "Prix par personne et par nuit.", ["Type de chambre", "1 personne", "2 personnes", "3 personnes"],
              ["Chambre standard", "Chambre confort"], "À noter : les prix incluent les taxes et le petit-déjeuner. Des conditions s'appliquent en cas de partage.", [120, 90, 150, 110, 95]),
        comp(p, 3, "sk-tiers1", [
            ("Support levels", "Niveaux de soutien"), ("Each level includes the benefits of the previous one.", "Chaque niveau inclut les avantages du précédent."),
            ("Level 1", "Niveau 1"), ("Level 2", "Niveau 2"), ("Level 3", "Niveau 3"),
            ("Everything in Friend", "Tout le niveau Ami"), ("Everything in Supporter", "Tout le niveau Soutien"),
            (">Friend<", ">Ami<"), (">Supporter<", ">Soutien<"), (">Patron<", ">Mécène<"),
            ("+ € 30", "+ 30 €"), ("+ € 60", "+ 60 €"), ("+ € 120", "+ 120 €"),
            ("Name on the supporters wall", "Votre nom sur le mur des soutiens"), ("Exclusive tote bag", "Tote bag exclusif"),
            ("Limited-edition T-shirt", "T-shirt en édition limitée"), ("Early access to ceremonies", "Accès anticipé aux cérémonies"), ("Reserved seating", "Places réservées")]),
        comp(p, 4, "sk-goodies1", [
            ("Collect them all.", "À collectionner !"), (">Hoodie<", ">Sweat<"), ("Luggage tag", "Étiquette de bagage"), (">Backpack<", ">Sac à dos<"), ("Travel pillow", "Oreiller de voyage"),
            ("Artist A", "Artiste A", ALL), ("Artist B", "Artiste B", ALL), ("Artist C", "Artiste C", ALL), ("Illustration:", "Illustration :", ALL),
            (">Level 1<", ">Niveau 1<", ALL), (">Level 2<", ">Niveau 2<", ALL), (">Level 3<", ">Niveau 3<", ALL)]),
        notice(p, 5, "À noter", "Tarifs communiqués à titre indicatif ; les niveaux de soutien s'ajoutent au prix du billet."),
        cta(p, 6, "Une question avant de réserver ?", "Consultez la FAQ ou contactez-nous.", "Voir la FAQ", "faq.html", "Nous contacter", "contact.html"),
        footer(p, 7)]

    p = "faq.html"
    pages[p] = [
        menu(p, 0),
        faq(p, 1, "Questions fréquentes", [
            ("Où se déroule le festival ?", "Au Centre des Congrès Rivage, 12 avenue de la Plage à Rivage-sur-Mer. Tous les détails d'accès sont sur la page « À propos »."),
            ("Puis-je être remboursé(e) ?", "Les billets sont remboursables jusqu'à trente jours avant l'événement, sur simple demande par e-mail."),
            ("Y a-t-il une limite d'âge ?", "Le festival est ouvert à tous. Les mineurs doivent être accompagnés d'un adulte."),
            ("Comment contacter l'équipe ?", "Utilisez le formulaire de la page Contact : nous répondons sous deux jours."),
            ("Puis-je venir en transports en commun ?", "Oui : le tram T2 et plusieurs lignes de bus desservent le centre des congrès."),
            ("Comment devenir bénévole ?", "Rendez-vous sur la page Recrutement et remplissez le formulaire.")]),
        cta(p, 2, "Une autre question ?", "Notre équipe vous répond avec plaisir.", "Nous contacter", "contact.html", "Voir les billets", "tickets.html"),
        footer(p, 3)]

    p = "register.html"
    pages[p] = [
        menu(p, 0),
        text(p, 1, "Inscription", "Suivez les quatre étapes ci-dessous pour réserver votre place. Le formulaire en bas de page nous permet de vous recontacter."),
        steps(p, 2, "Comment ça marche ?", 4),
        form(p, 3, "Demande d'inscription", "Nous vous répondons sous deux jours avec votre lien de paiement.", "Merci ! Votre demande a bien été envoyée.", phone=True),
        notice(p, 4, "À noter", "Les inscriptions ferment deux semaines avant le début du festival."),
        footer(p, 5)]

    p = "join-us.html"
    pages[p] = [
        menu(p, 0),
        text(p, 1, "Rejoignez le staff", "Le festival repose sur l'énergie de ses bénévoles. Découvrez les postes à pourvoir, puis remplissez le formulaire pour candidater."),
        comp(p, 2, "sk-positions1", [
            ("Open positions", "Postes à pourvoir"), ("Click a title to read the details.", "Cliquez sur un intitulé pour afficher le détail."),
            (">Safety ", ">Sécurité "), (">Logistics ", ">Logistique "), (">Operations ", ">Opérations "), (">Registration ", ">Accueil et inscriptions "), (">Technology ", ">Technique "),
            ("Key responsibilities", "Responsabilités clés", ALL), ("Skills and profile", "Compétences et profil", ALL),
            ("Before:", "Avant :", ALL), ("prepare and plan.", "préparer et planifier.", ALL), ("During:", "Pendant :", ALL), ("run the activity on site.", "animer l'activité sur place.", ALL),
            ("After:", "Après :", ALL), ("report and hand over.", "faire le bilan et transmettre.", ALL), ("Know-how:", "Savoir-faire :", ALL), ("relevant experience.", "expérience pertinente.", ALL),
            ("Soft skills:", "Savoir-être :", ALL), ("teamwork and reliability.", "esprit d'équipe et fiabilité.", ALL)], params={"jobs": 5}),
        comp(p, 3, "sk-perks1", [("Volunteer perks", "Avantages des bénévoles"), ("A reserved entry ticket", "Un billet d'entrée réservé"), ("Exclusive goodies", "Des goodies exclusifs"),
                                 ("Access to a staff lounge with snacks", "L'accès à une salle du staff avec collations"), ("And a few more surprises", "Et quelques surprises en plus"),
                                 ("Fill in the form to join the team", "Remplir le formulaire pour rejoindre le staff")], links=["contact.html"]),
        teams(p, 4, 6, ["COMPTABILITÉ", "SÉCURITÉ", "SCÈNE", "INFORMATIQUE", "LOGISTIQUE", "COMMUNICATION"]),
        footer(p, 5)]

    p = "contact.html"
    pages[p] = [
        menu(p, 0),
        form(p, 1, "Contactez-nous", "Nous répondons en général sous deux jours.", "Merci ! Votre message a bien été envoyé."),
        venue(p, 2, "Nous trouver", "Venez nous rendre visite au Centre des Congrès Rivage, en bord de mer.", side="left"),
        footer(p, 3)]

    p = "rules.html"
    pages[p] = [
        menu(p, 0),
        text(p, 1, "Règlement", "Merci de lire attentivement le règlement : il garantit un événement agréable et sûr pour tous."),
        faq(p, 2, "Règlement de l'événement", [
            ("Comportement", "Chacun doit respecter les autres participants, les bénévoles et le personnel du lieu. Tout comportement agressif ou discriminatoire est interdit."),
            ("Sécurité", "Les consignes du staff doivent être suivies en toutes circonstances. Les issues de secours doivent rester dégagées."),
            ("Objets interdits", "Les objets dangereux, les boissons en bouteille de verre et les animaux (hors chiens guides) ne sont pas admis."),
            ("Photos et vidéos", "Les prises de vue sont autorisées dans les espaces publics, sous réserve du consentement des personnes photographiées.")]),
        notice(p, 3, "Important", "Le non-respect du règlement peut entraîner une exclusion sans remboursement.", style="alert"),
        footer(p, 4)]

    p = "vendor-rules.html"
    pages[p] = [
        menu(p, 0),
        text(p, 1, "Règlement des exposants", "Conditions applicables aux exposants et aux créateurs présents dans l'espace marchand du festival."),
        table(p, 2, "Tarifs des emplacements", "Prix par emplacement pour les quatre jours.", ["Type d'emplacement", "1 table", "2 tables", "3 tables"],
              ["Emplacement standard", "Emplacement double"], "À noter : les installations électriques sont facturées en supplément.", [120, 90, 150, 110, 95]),
        notice(p, 3, "Important", "Les demandes d'emplacement sont traitées par ordre d'arrivée."),
        footer(p, 4)]

    p = "legal.html"
    pages[p] = [
        menu(p, 0),
        text(p, 1, "Mentions légales", "Éditeur : Association Horizon (exemple), 12 avenue de la Plage, 00000 Rivage-sur-Mer. Directeur de la publication : à compléter. Hébergeur : à compléter."),
        footer(p, 2)]

    # Tous les blocs, une fois chacun, avec leur contenu par défaut (page de test de l'extension)
    p = "all-blocks.html"
    pages[p] = [menu(p, 0)]
    for i, (g, path) in enumerate(sk.block_files(), start=1):
        key = os.path.splitext(os.path.basename(path))[0]
        if key in ("sk-menu1", "sk-footer2"):
            continue
        pages[p].append(comp(p, i, key))
    pages[p].append(footer(p, 99))
    return pages


pages = build_pages()
out = {"settings": copy.deepcopy(settings), "pages": {}}
for order, (file, comps) in enumerate(pages.items()):
    title, descr = PAGES[file]
    st = {"title": title, "meta_descr": descr}
    if file == "index.html":
        st = {"main": True, "title": title, "meta_descr": descr, "header_custom": "", "footer_custom": "", "html_before": ""}
    else:
        st["order"] = str(order)
    out["pages"][file] = {"settings": st, "components": comps}

s = out["settings"]
s["name"] = "Skyline Demo"
s["currentPage"] = "index.html"
s["uniqCompNum"] = _counter[0]
st = s["theme"]["styling"]
st.update({"primaryColor": "#080866", "secondaryColor": "#38bdf5", "mainFont": "Inter", "display1Font": "Shrikhand", "display2Font": "Shrikhand",
           "display5Font": "Inter", "display7Font": "Inter", "display4Font": "Inter", "underlinedLinks": False, "isAnimatedOnScroll": False,
           "display1Size": 3.5, "display2Size": 2.5, "display4Size": "1", "display5Size": 1.25, "display7Size": 1})
weights = ",".join("%d" % w for w in range(100, 1000, 100)) + "," + ",".join("%di" % w for w in range(100, 1000, 100))
s["siteFonts"] = [
    {"css": "'Shrikhand', sans-serif", "name": "Shrikhand", "url": "https://fonts.googleapis.com/css?family=Shrikhand:400"},
    {"css": "'Inter', sans-serif", "name": "Inter", "url": "https://fonts.googleapis.com/css?family=Inter:" + weights},
]

os.makedirs(os.path.dirname(args.out), exist_ok=True)
with open(args.out, "w", encoding="utf-8") as f:
    f.write(json.dumps(out, indent=2, ensure_ascii=False))
print("écrit", args.out, "-", len(out["pages"]), "pages,", sum(len(p["components"]) for p in out["pages"].values()), "blocs")
