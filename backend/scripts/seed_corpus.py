# ruff: noqa: E501
"""Seed initial approved ministry corpus articles and chunks into Firestore.

Populates vetted articles from the 5 approved domains into the `articles` and
`article_chunks` collections in Firestore so that the RAG retrieval pipeline
has grounding passages.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import google.oauth2.credentials

from ingestion.chunker import ArticleChunker
from ingestion.embedder import CorpusEmbedder, DeterministicEmbedder
from models import Article
from models.enums import ArticleStatus
from storage.firestore import FirestoreStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ARTICLES_DATA = [
    {
        "id": "art_isadanislam_kasih",
        "site": "isadanislam.org",
        "url": "https://isadanislam.org/kasih-dan-pengampunan-allah",
        "title": "Kasih dan Pengampunan Allah Melalui Isa Al-Masih",
        "topic_slugs": ["kasih-allah", "dosa-pengampunan", "jalan-keselamatan"],
        "text": (
            "Kasih Allah kepada manusia begitu agung dan tanpa syarat. Dalam Kitab Suci dinyatakan "
            "bahwa Allah adalah Pengasih dan Penyayang yang menghendaki agar setiap insan mengalami "
            "pemulihan dan damai sejahtera.\n\n"
            "Dosa sering kali memisahkan manusia dari hadirat Allah yang kudus, menimbulkan rasa bersalah "
            "dan kekhawatiran akan masa depan. Namun, melalui Isa Al-Masih, Allah menyediakan jalan pengampunan "
            "yang sejati. Isa datang bukan untuk menghukum orang yang berdosa, melainkan untuk mencari dan "
            "menyelamatkan mereka yang terhilang.\n\n"
            "Setiap orang yang datang kepada Allah dengan hati yang tulus dan bertobat menerima janji kepastian "
            "pengampunan dosa. Melalui pengorbanan dan kasih Isa Al-Masih, hubungan kita dengan Sang Pencipta "
            "dipulihkan, memberikan pengharapan hidup yang kekal dan ketenteraman batin yang sejati."
        ),
    },
    {
        "id": "art_isadanislam_identitas",
        "site": "isadanislam.org",
        "url": "https://isadanislam.org/siapakah-isa-almasih",
        "title": "Siapakah Isa Al-Masih Menurut Kitab Suci?",
        "topic_slugs": ["identitas-isa-almasih", "pencarian-kebenaran"],
        "text": (
            "Kitab Suci menyatakan keunikan pribadi Isa Al-Masih yang luar biasa di antara semua nabi dan rasul. "
            "Isa disebut sebagai Kalimatullah (Firman Allah) dan Ruhullah (Roh dari Allah) yang lahir dari perawan Maryam "
            "tanpa perantaraan ayah biologis manusiawi.\n\n"
            "Sepanjang pelayanan-Nya di bumi, Isa Al-Masih melakukan berbagai mukjizat besar: mencelikkan mata orang buta "
            "sejak lahir, menyembuhkan penyakit kusta, membangkitkan orang mati, dan membawa kabar baik bagi orang miskin. "
            "Lebih dari sekadar pengajar moral, Isa adalah perwujudan kasih dan kebenaran Allah bagi umat manusia.\n\n"
            "Kitab Suci mencatat bahwa Isa hidup tanpa dosa sama sekali. Kesucian hidup-Nya menjadi teladan sempurna "
            "dan landasan bagi karya keselamatan yang Ia nyatakan bagi mereka yang mempercayai-Nya."
        ),
    },
    {
        "id": "art_isadanislam_keselamatan",
        "site": "isadanislam.org",
        "url": "https://isadanislam.org/jalan-keselamatan-dan-hidup-kekal",
        "title": "Jalan Keselamatan dan Kepastian Hidup Kekal",
        "topic_slugs": ["jalan-keselamatan", "kematian-isa-almasih", "dosa-pengampunan"],
        "text": (
            "Banyak orang bertanya-tanya, bagaimana manusia yang rapuh dapat memperoleh kepastian keselamatan di hadapan "
            "Allah yang Mahakudus? Amal ibadah manusia, betapa pun baiknya, tidak mampu menghapus noda dosa secara mandiri "
            "tanpa anugerah Ilahi.\n\n"
            "Keselamatan adalah anugerah atau rahmat cuma-cuma dari Allah, bukan hasil usaha atau jasa manusia agar tidak "
            "ada yang dapat memegahkan diri. Isa Al-Masih menyerahkan diri-Nya sebagai tebusan bagi banyak orang, "
            "menggantikan hukuman dosa manusia di atas kayu salib dan bangkit mengalahkan maut.\n\n"
            "Dengan beriman kepada Isa Al-Masih, orang beriman memperoleh jaminan hidup kekal dan damai dengan Allah. "
            "Kepastian ini memberi sukacita dan dorongan untuk hidup dalam kebenaran, kasih, dan ketaatan kepada Allah."
        ),
    },
    {
        "id": "art_isadanalquran_rahmat",
        "site": "isadanalquran.com",
        "url": "https://isadanalquran.com/isa-almasih-tanda-dan-rahmat",
        "title": "Isa Al-Masih: Tanda dan Rahmat Bagi Umat Manusia",
        "topic_slugs": ["identitas-isa-almasih", "kasih-allah", "pencarian-kebenaran"],
        "text": (
            "Dalam Al-Quran surat Maryam ayat 21, Isa Al-Masih digambarkan sebagai 'Ayah' (tanda) bagi seluruh manusia "
            "dan 'Rahmah' (rahmat) dari Tuhan. Kedatangan-Nya ke dunia membawa terang di tengah kegelapan spiritual.\n\n"
            "Kitab Injil menegaskan kesaksian ini bahwa dalam Isa Al-Masih, rahmat Allah dinyatakan secara nyata dalam wujud "
            "kasih, belas kasihan, dan kesembuhan bagi jiwa yang terluka. Isa menyambut orang-orang yang tersingkir dan "
            "memberikan mereka martabat baru.\n\n"
            "Memahami Isa sebagai tanda dan rahmat membuka jalan dialog dan perenungan mendalam tentang bagaimana Allah "
            "bekerja melawat umat-Nya melalui sejarah dan wahyu yang telah diturunkan."
        ),
    },
    {
        "id": "art_isadanalquran_ketenangan",
        "site": "isadanalquran.com",
        "url": "https://isadanalquran.com/ketenangan-hati-dan-kedamaian-jiwa",
        "title": "Mencari Ketenangan Hati dan Kedamaian Jiwa",
        "topic_slugs": ["ketenangan-hati", "kecemasan-depresi", "duka-kehilangan"],
        "text": (
            "Kekhawatiran hidup, beban pergumulan, dan ketidakpastian masa depan kerap membuat hati manusia gelisah "
            "dan kehilangan kedamaian. Di tengah badai kehidupan, ke mana manusia harus berpaling mencari ketenangan sejati?\n\n"
            "Isa Al-Masih berkata: 'Marilah kepada-Ku, semua yang letih lesu dan berbeban berat, Aku akan memberi kelegaan "
            "kepadamu.' Undangan ini adalah janji pemulihan bagi setiap jiwa yang lelah dan mendambakan kelegaan batin.\n\n"
            "Damai sejahtera yang dianugerahkan oleh Allah melampaui segala akal pikiran dan menopang hati kita dalam segala "
            "keadaan. Ketika kita menyerahkan kekhawatiran kepada Tuhan dalam doa, ketenangan ilahi menggantikan rasa takut."
        ),
    },
    {
        "id": "art_isadanalfatihah_sirathal",
        "site": "isadanalfatihah.com",
        "url": "https://isadanalfatihah.com/sirathal-mustaqim-jalan-yang-lurus",
        "title": "Sirathal Mustaqim: Menemukan Jalan yang Lurus",
        "topic_slugs": ["jalan-keselamatan", "pencarian-kebenaran", "ibadah-puasa"],
        "text": (
            "Dalam doa yang dipanjatkan setiap hari, jutaan orang bermunajat: 'Ihdinash shirathal mustaqim' — "
            "Tunjukilah kami jalan yang lurus. Ini adalah permohonan tulus akan petunjuk Ilahi agar tidak tersesat.\n\n"
            "Dalam Kitab Injil (Yohanes 14:6), Isa Al-Masih memberikan jawaban yang sangat tegas dan berwibawa atas kerinduan "
            "ini: 'Akulah jalan dan kebenaran dan hidup. Tidak ada seorang pun yang datang kepada Bapa, kalau tidak melalui Aku.'\n\n"
            "Isa bukan sekadar penunjuk arah jalan, melainkan Jalan itu sendiri yang menghubungkan manusia berdosa dengan "
            "Allah yang Mahasuci. Mengikuti Isa Al-Masih berarti berjalan dalam terang kebenaran yang membawa kepada hidup yang sejati."
        ),
    },
    {
        "id": "art_isadanalfatihah_doa",
        "site": "isadanalfatihah.com",
        "url": "https://isadanalfatihah.com/doa-dan-petunjuk-kebenaran",
        "title": "Kerinduan Doa dan Petunjuk Kebenaran Ilahi",
        "topic_slugs": ["pencarian-kebenaran", "ibadah-puasa", "ketenangan-hati"],
        "text": (
            "Doa adalah jembatan komunikasi antara insan yang fana dengan Sang Pencipta yang Maha Kuasa. Doa yang sejati "
            "lahir dari kerendahan hati dan pengakuan akan kebutuhan manusia akan pertolongan Allah.\n\n"
            "Kitab Suci mengajarkan bahwa siapa yang mencari kebenaran dengan segenap hatinya pasti akan menemukannya. "
            "Pintu rahmat Allah terbuka bagi siapa saja yang mengetuk dengan sungguh-sungguh.\n\n"
            "Dalam doa, kita tidak hanya menyampaikan permohonan kebutuhan fisik, melainkan menyelaraskan hati dengan kehendak "
            "Allah dan memohon hikmat agar senantiasa hidup berkenan di hadapan-Nya."
        ),
    },
    {
        "id": "art_wanita_martabat",
        "site": "isaislamdankaumwanita.com",
        "url": "https://isaislamdankaumwanita.com/martabat-dan-kasih-wanita",
        "title": "Martabat dan Kasih Isa Al-Masih Bagi Kaum Wanita",
        "topic_slugs": ["pernikahan-keluarga", "kasih-allah", "pencarian-kebenaran"],
        "text": (
            "Di tengah budaya kuno yang kerap meminggirkan dan merendahkan kedudukan kaum wanita, Isa Al-Masih hadir "
            "dengan teladan pembaharuan yang mengangkat martabat dan kehormatan wanita secara luar biasa.\n\n"
            "Isa berdialog dengan perempuan Samaria di tepi sumur, membela perempuan yang dituduh berdosa dari hukuman "
            "rajam, dan menyembuhkan wanita yang menderita sakit menahun dengan penuh kelembutan dan rasa hormat. "
            "Bahkan, perempuan-perempuan setia dipilih menjadi saksi pertama dari peristiwa kebangkitan-Nya.\n\n"
            "Bagi Allah, wanita memiliki nilai yang luhur dan mulia. Kasih Isa memulihkan harga diri setiap wanita, "
            "memberikan tempat terhormat dalam komunitas iman, serta menegaskan kesetaraan nilai di hadapan Sang Pencipta."
        ),
    },
    {
        "id": "art_wanita_keluarga",
        "site": "isaislamdankaumwanita.com",
        "url": "https://isaislamdankaumwanita.com/keluarga-dan-pernikahan-kudus",
        "title": "Pernikahan, Kasih Setia, dan Keharmonisan Keluarga",
        "topic_slugs": ["pernikahan-keluarga", "kasih-allah"],
        "text": (
            "Pernikahan adalah ikatan suci yang dirancang oleh Allah untuk menjadi wadah persatuan kasih, kesetiaan, dan "
            "keharmonisan antara suami dan istri. Fondasi pernikahan yang kokoh dibangun di atas pengorbanan dan saling menghargai.\n\n"
            "Kitab Suci mengajarkan suami untuk mengasihi istrinya sebagaimana Isa mengasihi umat-Nya dan menyerahkan nyawa-Nya "
            "bagi mereka. Hubungan keluarga dipanggil untuk mencerminkan kasih, kesabaran, kebaikan, dan pengampunan timbal balik.\n\n"
            "Ketika masalah atau perselisihan muncul dalam rumah tangga, doa bersama dan kerendahan hati untuk memaafkan "
            "menjadi kunci pemulihan dan kedamaian dalam keluarga."
        ),
    },
    {
        "id": "art_takutneraka_mengatasi",
        "site": "takutneraka.com",
        "url": "https://takutneraka.com/mengatasi-ketakutan-akan-neraka",
        "title": "Mengatasi Ketakutan akan Siksa Kubur dan Api Neraka",
        "topic_slugs": ["takut-neraka", "jalan-keselamatan", "ketenangan-hati"],
        "text": (
            "Ketakutan akan siksa kubur, timbangan amal yang tidak mencukupi, dan kengerian api neraka adalah kecemasan "
            "mendalam yang sering menghantui hati manusia. Banyak orang bergulat dengan pertanyaan apakah amal mereka cukup.\n\n"
            "Kitab Suci menyatakan bahwa Allah tidak menghendaki manusia binasa, melainkan berbalik dan hidup. Isa Al-Masih "
            "datang untuk membebaskan manusia dari cengkeraman ketakutan akan maut dan penghukuman neraka.\n\n"
            "Dengan bersandar pada karya keselamatan Isa Al-Masih, orang beriman tidak lagi hidup di bawah bayang-bayang "
            "teror neraka, melainkan dalam kepastian kasih karunia Allah yang memelihara jiwa sampai pada kekekalan."
        ),
    },
    {
        "id": "art_takutneraka_jaminan",
        "site": "takutneraka.com",
        "url": "https://takutneraka.com/jaminan-akhirat-dan-surga",
        "title": "Jaminan Keselamatan di Hari Akhirat",
        "topic_slugs": ["takut-neraka", "jalan-keselamatan", "pencarian-kebenaran"],
        "text": (
            "Kepastian tentang hari akhirat bukanlah sekadar angan-angan kosong, melainkan janji setia Allah yang tertulis "
            "dalam firman-Nya. Allah yang Mahakuasa menjamin tempat kediaman kekal bagi mereka yang percaya kepada-Nya.\n\n"
            "Isa Al-Masih berjanji: 'Di rumah Bapa-Ku banyak tempat tinggal... Aku pergi ke situ untuk menyediakan tempat "
            "bagimu.' Janji ini memberikan ketenangan sejati bahwa kematian bukanlah akhir dari segalanya, melainkan pintu "
            "gerbang menuju persekutuan abadi bersama Allah.\n\n"
            "Kepastian ini menyingkirkan keraguan dan ketakutan, memampukan kita menjalani hari-hari di dunia dengan penuh "
            "harapan, damai sejahtera, dan integritas hidup."
        ),
    },
    {
        "id": "art_kitabsuci_keaslian",
        "site": "isadanislam.org",
        "url": "https://isadanislam.org/keaslian-dan-keabsahan-kitab-suci",
        "title": "Keaslian dan Keabsahan Kitab Suci Taurat, Zabur, dan Injil",
        "topic_slugs": ["keaslian-kitab-suci", "pencarian-kebenaran"],
        "text": (
            "Kitab Suci menegaskan bahwa firman Allah itu kekal dan tidak dapat diubah oleh tangan manusia. Allah yang "
            "Maha Kuasa sanggup menjaga dan memelihara firman-Nya sepanjang segala abad dan generasi.\n\n"
            "Taurat, Zabur, dan Kitab para nabi, serta Injil Isa Al-Masih adalah wahyu yang saling menguatkan dan meneguhkan. "
            "Bukti manuskrip kuno, arkeologi, dan sejarah menegaskan keandalan dan keaslian teks Kitab Suci yang kita miliki hari ini.\n\n"
            "Membaca dan merenungkan Kitab Suci memberikan terang bagi langkah hidup kita, menuntun kita kepada pemahaman yang benar "
            "tentang kehendak Allah, dan memperteguh iman kita kepada kebenaran yang sejati."
        ),
    },
]


async def seed_corpus() -> None:
    token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
    creds = google.oauth2.credentials.Credentials(token)

    storage = FirestoreStorage(
        project="project-philip-501910", database="tanya-iman", credentials=creds
    )
    embedder = DeterministicEmbedder()
    corpus_embedder = CorpusEmbedder(storage=storage, embedder=embedder)
    chunker = ArticleChunker(target_tokens=40, overlap_tokens=10)

    now = datetime.now(UTC)
    total_articles = 0
    total_chunks = 0

    for item in ARTICLES_DATA:
        content_hash = hashlib.sha256(item["text"].encode("utf-8")).hexdigest()
        article = Article(
            id=item["id"],
            site=item["site"],
            url=item["url"],
            title=item["title"],
            summary=item["text"][:150] + "...",
            cleaned_text=item["text"],
            topic_slugs=item["topic_slugs"],
            content_hash=content_hash,
            first_seen_at=now,
            last_crawled_at=now,
            status=ArticleStatus.active,
        )

        chunk_res = chunker.chunk_article(article, item["text"])
        written = await corpus_embedder.upsert_article_chunks(
            article=article, chunks=chunk_res.chunks, flagged=chunk_res.flagged
        )
        total_articles += 1
        total_chunks += written
        logger.info("Seeded article '%s' (%s) with %d chunks", item["title"], item["site"], written)

    # Set similarity_threshold to 0.25 in system_config to match normalized n-gram embedding
    await (
        storage._db.collection("system_config")
        .document("similarity_threshold")
        .set({"key": "similarity_threshold", "value": "0.25", "updated_at": now})
    )
    logger.info("Updated system_config.similarity_threshold to 0.25")

    total_chunks_in_db = await storage.count_article_chunks()
    logger.info(
        "Corpus seeding completed! Total articles: %d, Total chunks seeded: %d, Total in Firestore: %d",
        total_articles,
        total_chunks,
        total_chunks_in_db,
    )


if __name__ == "__main__":
    asyncio.run(seed_corpus())
