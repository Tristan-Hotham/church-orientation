"""Extract the patron saint (or dedication) from an OpenStreetMap church name or dedication tag."""
import re

# canonical saint names; keys are lower-case variants found in names
CANON = {
    'mary': 'Mary', 'our lady': 'Mary', 'blessed virgin mary': 'Mary', 'the blessed virgin mary': 'Mary', 'virgin mary': 'Mary',
    'st mary the virgin': 'Mary', 'mary the virgin': 'Mary', 'bvm': 'Mary', 'mary and': 'Mary', 'marys': 'Mary', 'lady': 'Mary',
    'all saints': 'All Saints', 'all hallows': 'All Saints', 'allhallows': 'All Saints',
    'peter': 'Peter', 'paul': 'Paul', 'peter and paul': 'Peter and Paul', 'peter and st paul': 'Peter and Paul', 'peter & paul': 'Peter and Paul',
    'michael': 'Michael', 'michael and all angels': 'Michael', 'michael & all angels': 'Michael',
    'andrew': 'Andrew', 'john the baptist': 'John the Baptist', 'john baptist': 'John the Baptist', 'john': 'John',
    'john the evangelist': 'John the Evangelist', 'nicholas': 'Nicholas', 'margaret': 'Margaret', 'james': 'James',
    'james the great': 'James', 'lawrence': 'Lawrence', 'laurence': 'Lawrence', 'leonard': 'Leonard', 'giles': 'Giles',
    'helen': 'Helen', 'holy trinity': 'Holy Trinity', 'trinity': 'Holy Trinity', 'christ church': 'Christ Church',
    'bartholomew': 'Bartholomew', 'botolph': 'Botolph', 'botolf': 'Botolph', 'george': 'George', 'martin': 'Martin',
    'luke': 'Luke', 'mark': 'Mark', 'matthew': 'Matthew', 'stephen': 'Stephen', 'thomas': 'Thomas', 'thomas a becket': 'Thomas Becket',
    'thomas becket': 'Thomas Becket', 'thomas of canterbury': 'Thomas Becket', 'edmund': 'Edmund', 'oswald': 'Oswald',
    'cuthbert': 'Cuthbert', 'chad': 'Chad', 'wilfrid': 'Wilfrid', 'wilfred': 'Wilfrid', 'aidan': 'Aidan', 'hilda': 'Hilda',
    'david': 'David', 'dewi': 'David', 'teilo': 'Teilo', 'cadoc': 'Cadoc', 'cattwg': 'Cadoc', 'beuno': 'Beuno', 'tysilio': 'Tysilio',
    'petroc': 'Petroc', 'piran': 'Piran', 'perran': 'Piran', 'columba': 'Columba', 'ninian': 'Ninian', 'kentigern': 'Kentigern',
    'mungo': 'Kentigern', 'brigid': 'Bride', 'bride': 'Bride', 'bridget': 'Bride', 'brides': 'Bride', 'ffraid': 'Bride',
    'patrick': 'Patrick', 'swithun': 'Swithun', 'swithin': 'Swithun', 'dunstan': 'Dunstan', 'alban': 'Alban', 'augustine': 'Augustine',
    'etheldreda': 'Etheldreda', 'audrey': 'Etheldreda', 'werburgh': 'Werburgh', 'mary magdalene': 'Mary Magdalene',
    'mary magdalen': 'Mary Magdalene', 'magdalene': 'Mary Magdalene', 'magdalen': 'Mary Magdalene', 'catherine': 'Catherine',
    'katharine': 'Catherine', 'katherine': 'Catherine', 'anne': 'Anne', 'clement': 'Clement', 'denys': 'Denys', 'denis': 'Denys',
    'edward': 'Edward', 'edward the confessor': 'Edward', 'faith': 'Faith', 'germanus': 'Germanus', 'gregory': 'Gregory',
    'hilary': 'Hilary', 'jude': 'Jude', 'simon and st jude': 'Simon and Jude', 'simon and jude': 'Simon and Jude',
    'philip': 'Philip', 'philip and st james': 'Philip and James', 'barnabas': 'Barnabas', 'saviour': 'Saviour', 'holy cross': 'Holy Cross',
    'holy rood': 'Holy Cross', 'holy spirit': 'Holy Spirit', 'holy ghost': 'Holy Spirit', 'emmanuel': 'Emmanuel', 'immanuel': 'Emmanuel',
    'kenelm': 'Kenelm', 'guthlac': 'Guthlac', 'wystan': 'Wystan', 'bega': 'Bega', 'bees': 'Bega', 'kentigern': 'Kentigern',
    'machutus': 'Malo', 'mewan': 'Mewan', 'mawgan': 'Mawgan', 'tudy': 'Tudy', 'issey': 'Issey', 'neot': 'Neot', 'brannock': 'Brannock',
    'nectan': 'Nectan', 'decuman': 'Decuman', 'bueno': 'Beuno', 'cybi': 'Cybi', 'illtud': 'Illtud', 'illtyd': 'Illtud',
    'padarn': 'Padarn', 'deiniol': 'Deiniol', 'tydfil': 'Tydfil', 'gwynllyw': 'Gwynllyw', 'woolos': 'Gwynllyw', 'mungo': 'Kentigern',
    'machar': 'Machar', 'serf': 'Serf', 'fillan': 'Fillan', 'kessog': 'Kessog', 'moluag': 'Moluag', 'maelrubha': 'Maelrubha',
    'drostan': 'Drostan', 'ternan': 'Ternan', 'fergus': 'Fergus', 'blane': 'Blane', 'cuthbert': 'Cuthbert', 'boswell': 'Boisil',
    'margaret of scotland': 'Margaret', 'mirren': 'Mirin', 'mirin': 'Mirin', 'conval': 'Conval', 'monan': 'Monan', 'ethelbert': 'Ethelbert',
    'ethelburga': 'Ethelburga', 'frideswide': 'Frideswide', 'birinus': 'Birinus', 'aldhelm': 'Aldhelm', 'juliot': 'Julitta',
    'julitta': 'Julitta', 'helier': 'Helier', 'sampson': 'Samson', 'samson': 'Samson', 'winwaloe': 'Winwaloe', 'cyriac': 'Cyriac',
    'cyr': 'Cyriac', 'quiricus': 'Cyriac', 'eanswythe': 'Eanswythe', 'mildred': 'Mildred', 'pancras': 'Pancras', 'osyth': 'Osyth',
    'cedd': 'Cedd', 'felix': 'Felix', 'fursey': 'Fursey', 'wendreda': 'Wendreda', 'withburga': 'Withburga', 'everilda': 'Everilda',
    'everild': 'Everilda', 'oswin': 'Oswin', 'paulinus': 'Paulinus', 'wulfram': 'Wulfram', 'hybald': 'Hybald', 'helen of': 'Helen',
    'eata': 'Eata', 'ebba': 'Ebba', 'bee': 'Bega', 'herbert': 'Herbert', 'kentigern and': 'Kentigern', 'kevin': 'Kevin', 'petrock': 'Petroc', 'mair': 'Mary', 'fair': 'Mary', 'pedr': 'Peter', 'mihangel': 'Michael', 'fihangel': 'Michael', 'ioan': 'John', 'iago': 'James', 'andreas': 'Andrew', 'tomos': 'Thomas', 'catrin': 'Catherine', 'ann': 'Anne', 'elen': 'Helen', 'sior': 'George', 'pawl': 'Paul', 'luc': 'Luke', 'marc': 'Mark', 'mathew': 'Matthew', 'mathias': 'Matthias', 'stephan': 'Stephen', 'tudno': 'Tudno', 'tysul': 'Tysul', 'dyfrig': 'Dyfrig', 'dubricius': 'Dyfrig', 'tegla': 'Tegla', 'winefride': 'Winefride', 'gwenfrewi': 'Winefride', 'non': 'Non', 'nonna': 'Non', 'brynach': 'Brynach', 'mary the virgin': 'Mary',
}
GENERIC = {'all st':'All Saints','yr holl saint':'All Saints','holl saint':'All Saints','y drindod':'Holy Trinity','drindod':'Holy Trinity','all sts':'All Saints','holy trinity':'Holy Trinity','trinity':'Holy Trinity','christ church':'Christ Church','christchurch':'Christ Church','emmanuel':'Emmanuel','immanuel':'Emmanuel','holy cross':'Holy Cross','holy rood':'Holy Cross','sacred heart':'Sacred Heart','christ the king':'Christ the King','good shepherd':'Good Shepherd','ascension':'Ascension','holy spirit':'Holy Spirit','holy ghost':'Holy Spirit','all saints':'All Saints','all saint':'All Saints','all hallows':'All Saints','holy family':'Holy Family','our lady':'Mary','annunciation':'Annunciation','epiphany':'Epiphany','transfiguration':'Transfiguration','resurrection':'Resurrection','holy redeemer':'Holy Redeemer','redeemer':'Holy Redeemer','holy name':'Holy Name','holy innocents':'Holy Innocents','saviour':'Saviour'}
SKIP = {'church', 'parish', 'and', 'the', 'of', 'chapel', 'cathedral', 'minster', 'abbey', 'priory', 'mission', 'hall', 'centre'}


def saint(name, dedication=None):
    """Return a canonical dedication for a church, or None."""
    for src in (dedication, name):
        if not src:
            continue
        s = src.lower().replace('’', "'")
        s = re.sub(r"\b(saint|sts|ss|san|santa|sant|santes|seintiau|sain)\b\.?", 'st', s)
        s = re.sub(r"\beglwys\b", 'church', s)
        s = re.sub(r"\bst\.", 'st', s)
        s = re.sub(r"'s\b|s'\b", '', s)
        s = re.sub(r"[^a-z& ]", ' ', s).replace('&', ' and ')
        s = re.sub(r"\s+", ' ', s).strip()
        # specific phrases first
        for k in sorted(CANON, key=len, reverse=True):
            if len(k.split()) > 1 and re.search(r'\b' + re.escape(k) + r'\b', s):
                return CANON[k]
        m = re.search(r'\bst ([a-z]+)', s)
        if m:
            w = m.group(1)
            if w in CANON:
                return CANON[w]
            if w.endswith('s') and w[:-1] in CANON:
                return CANON[w[:-1]]
        m2 = re.search(r'\b([a-z]+) st\b', s)
        if m2 and m2.group(1) in CANON:
            return CANON[m2.group(1)]
        for k in sorted(GENERIC, key=len, reverse=True):
            if re.search(r'\b' + re.escape(k) + r'\b', s):
                return GENERIC[k]
        if m and m.group(1) not in SKIP and len(m.group(1)) > 2:
            w = m.group(1)
            return w.title()
        if src is dedication and s:
            w = s.split()[0]
            if w in CANON:
                return CANON[w]
    return None
