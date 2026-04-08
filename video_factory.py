"""
VIDEO FACTORY - Automated German YouTube Video Production
==========================================================
Complete pipeline: Script -> TTS -> Video -> Upload

Usage:
    python3 video_factory.py                     # Interactive mode
    python3 video_factory.py --batch scripts/     # Batch mode from JSON scripts
"""

import os
import sys
import json
import argparse
from config import *
from generate_video import generate_video
from upload_video import upload_video


# Pre-made German video scripts based on top-performing topics
SAMPLE_SCRIPTS = [
    {
        "title_de": "Wie Frauen den Wert des Mannes erkennen, den sie als selbstverstaendlich betrachteten | Weibliche Psychologie",
        "description_de": """Hast du dich jemals gefragt, warum Frauen erst dann den wahren Wert eines Mannes erkennen, wenn er nicht mehr da ist?

In diesem Video erklaeren wir die Psychologie hinter diesem Phaenomen und warum es so haeufig vorkommt.

Du lernst:
- Warum Frauen gute Maenner oft als selbstverstaendlich betrachten
- Die psychologischen Phasen der Reue nach dem Verlust
- Wie du dein Selbstwertgefuehl staerkst
- Warum Schweigen maechtiger ist als Worte

#WeiblichePsychologie #Beziehungspsychologie #SelbstverbesserungMaenner #MaennlicheStaerke #EmotionaleHeilung #DatingTippsDeutsch #Beziehungsberatung #PsychologieDeutsch #TrennungUeberwinden #Selbstbewusstsein

Abonniere fuer taegliche Videos ueber Beziehungspsychologie und persoenliches Wachstum!""",
        "tags_de": [
            "wie frauen maenner vermissen",
            "weibliche psychologie deutsch",
            "selbstverstaendlich genommen",
            "beziehung psychologie",
            "maenner selbstverbesserung",
            "trennung verarbeiten",
            "sie bereut es",
            "nach trennung staerker",
        ],
        "script_de": """Ich moechte heute ueber etwas sprechen, das vielen Maennern passiert, aber selten wirklich verstanden wird. Wenn eine Frau einen guten Mann verliert, passiert etwas Tiefgreifendes in ihrem Unterbewusstsein.

Zunaechst scheint es, als waere nichts passiert. Sie geht ihrem Leben nach, vielleicht trifft sie sogar andere Menschen. Aber mit der Zeit beginnt etwas zu bröckeln.

Die Realitaet des Verlustes setzt nicht sofort ein. Das Gehirn schuetzt sich selbst. Es vermeidet den Schmerz, indem es die Bedeutung dessen, was verloren ging, herunterspielt. Aber die Wahrheit kommt immer ans Licht.

In der Psychologie nennen wir das den Kontrasteffekt. Erst wenn jemand neues in ihr Leben tritt, der nicht das gleiche Mass an Respekt, Aufmerksamkeit und emotionaler Sicherheit bietet, erkennt sie, was sie hatte.

Das ist der Moment, in dem die Reue beginnt. Nicht sofort, sondern schleichend. Wie ein Schatten, der laenger wird, je weiter die Sonne sinkt.

Die erste Phase ist die Verleugnung. Sie erzaehlt sich selbst, dass es die richtige Entscheidung war. Sie konzentriert sich auf die negativen Aspekte der Beziehung, auf die kleinen Dinge, die sie gestoert haben.

Aber dann kommt Phase zwei: Der Vergleich. Jeder Mann, den sie trifft, wird unbewusst an dir gemessen. Und die meisten werden nicht bestehen. Nicht weil sie schlechte Menschen sind, sondern weil du einen Standard gesetzt hast, den sie nicht erkannt hat, als du noch da warst.

Phase drei ist die tiefste: Die Erkenntnis. Sie versteht nun, dass die Ruhe, die du gebracht hast, keine Langweile war. Dass deine Bestaendigkeit keine Selbstverstaendlichkeit war. Dass deine stille Staerke ein Geschenk war, das sie nicht zu schaetzen wusste.

Aber hier ist die wichtigste Lektion fuer dich als Mann. Diese Erkenntnis ist nicht deine Verantwortung. Deine einzige Aufgabe ist es, weiterzuwachsen. Staerker zu werden. Nicht um ihr etwas zu beweisen, sondern um dir selbst zu zeigen, was du wert bist.

Denn wahre Staerke liegt nicht darin, jemanden zurueckzugewinnen. Wahre Staerke liegt darin, sich selbst zurueckzugewinnen. Und wenn du das tust, wird sich alles andere von selbst ergeben.

Denk daran: Du musst niemanden ueberzeugen, dass du wertvoll bist. Die richtigen Menschen werden es erkennen. Und diejenigen, die es nicht tun, waren nie fuer dich bestimmt.""",
    },
    {
        "title_de": "Wenn eine Frau dich nicht respektiert, aendert dieser eine Schritt alles | Weibliche Psychologie",
        "description_de": """Respektlosigkeit in einer Beziehung ist eines der zerstoererischsten Muster. Aber die meisten Maenner reagieren falsch darauf.

In diesem Video lernst du:
- Warum Erklaerungen und Bitten den Respekt NICHT zurueckbringen
- Die eine Handlung, die alles veraendert
- Wie Schweigen maaechtiger ist als jedes Wort
- Die Psychologie hinter weiblichem Respekt

#WeiblichePsychologie #RespektInBeziehungen #MaennlicheStaerke #Beziehungspsychologie #SelbstrespektMaenner

Abonniere fuer taegliche Videos!""",
        "tags_de": [
            "wenn sie dich nicht respektiert",
            "respekt zurueckgewinnen",
            "weibliche psychologie respekt",
            "maennliche staerke",
            "beziehung respekt",
            "schweigen macht",
            "selbstrespekt maenner",
        ],
        "script_de": """Es gibt eine Wahrheit, die die meisten Maenner nicht hoeren wollen. Aber wenn du sie einmal verstehst, wird sie dein gesamtes Beziehungsleben veraendern.

Wenn eine Frau aufhoert, dich zu respektieren, ist die erste Reaktion der meisten Maenner, zu erklaeren. Zu argumentieren. Zu bitten. Zu beweisen. Aber genau das ist der Fehler.

Jedes Mal, wenn du versuchst, jemanden davon zu ueberzeugen, dich zu respektieren, verlierst du genau das, worum du bittest. Respekt kann nicht erbeten werden. Er kann nur verdient und manchmal zurueckgefordert werden. Aber niemals durch Worte.

Die Psychologie dahinter ist einfach, aber tiefgreifend. Respekt basiert auf wahrgenommenem Wert. Und Wert wird nicht durch das kommuniziert, was du sagst, sondern durch das, was du tust. Oder noch maechtiger: durch das, was du nicht tust.

Wenn eine Frau die Grenzen ueberschreitet und du nichts sagst, lernt sie, dass es keine Grenzen gibt. Wenn sie dich schlecht behandelt und du bleibst, lernt sie, dass du es akzeptierst.

Der eine Schritt, der alles veraendert, ist nicht Konfrontation. Es ist nicht Wut. Es ist nicht Drama. Es ist stille Distanz.

Du ziehst dich zurueck. Nicht aus Strafe, sondern aus Selbstrespekt. Du reduzierst deine Verfuegbarkeit. Du konzentrierst dich auf dich selbst. Du machst deutlich, ohne ein Wort zu sagen, dass du deine eigene Gesellschaft der Respektlosigkeit vorziehst.

Das ist der Moment, in dem sich alles verschiebt. Denn ploetzlich erkennt sie etwas Wichtiges: Du brauchst sie nicht. Du waehlst sie. Und es gibt einen gewaltigen Unterschied zwischen Beduerftigkeit und bewusster Wahl.

Respekt kommt zurueck, wenn eine Frau versteht, dass du bereit bist, zu gehen. Nicht als Drohung, nicht als Manipulation, sondern als echte innere Ueberzeugung, dass du lieber allein bist als schlecht behandelt zu werden.

Das ist wahre maennliche Staerke. Nicht laut, nicht aggressiv, nicht kontrollierend. Sondern ruhig, sicher und unerschuetterlich in deinem Selbstwert.""",
    },
]


def create_script_file(script_data, output_dir):
    """Save a script to JSON file for batch processing."""
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in script_data["title_de"])[:40].strip()
    safe_name = safe_name.replace(" ", "_")
    filepath = os.path.join(output_dir, f"{safe_name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2, ensure_ascii=False)
    return filepath


def process_single(script_data, avatar_path, upload=False, privacy="private", token_file=None):
    """Process a single video: generate + optionally upload."""
    
    video_path = generate_video(
        script_text=script_data["script_de"],
        title_de=script_data["title_de"],
        avatar_image=avatar_path,
    )
    
    if video_path and upload:
        video_id = upload_video(
            video_path=video_path,
            title_de=script_data["title_de"],
            description_de=script_data["description_de"],
            tags_de=script_data["tags_de"],
            privacy=privacy,
            token_file=token_file,
        )
        return video_id
    
    return video_path


def batch_process(scripts_dir, avatar_path, upload=False, privacy="private", token_file=None):
    """Process all JSON script files in a directory."""
    
    script_files = sorted([f for f in os.listdir(scripts_dir) if f.endswith(".json")])
    print(f"\nFound {len(script_files)} script(s) to process")
    
    results = []
    for i, sf in enumerate(script_files, 1):
        print(f"\n{'#'*60}")
        print(f"Processing [{i}/{len(script_files)}]: {sf}")
        print(f"{'#'*60}")
        
        with open(os.path.join(scripts_dir, sf), encoding="utf-8") as f:
            script_data = json.load(f)
        
        result = process_single(script_data, avatar_path, upload, privacy, token_file)
        results.append({"file": sf, "result": result})
    
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE: {len(results)} videos processed")
    for r in results:
        status = "OK" if r["result"] else "FAILED"
        print(f"  [{status}] {r['file']}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="German YouTube Video Factory")
    parser.add_argument("--batch", help="Directory with JSON script files")
    parser.add_argument("--avatar", default=os.path.join(AVATARS_DIR, "avatar.png"), help="Avatar image path")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube after generation")
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    parser.add_argument("--token", default=TOKEN_FILE, help="Token file to use")
    parser.add_argument("--save-samples", action="store_true", help="Save sample scripts to scripts/ dir")
    
    args = parser.parse_args()
    
    if args.save_samples:
        print("Saving sample scripts...")
        os.makedirs(SCRIPTS_DIR, exist_ok=True)
        for script in SAMPLE_SCRIPTS:
            path = create_script_file(script, SCRIPTS_DIR)
            print(f"  Saved: {path}")
        print("Done! Edit these files, then run with --batch scripts/")
        return
    
    if args.batch:
        batch_process(args.batch, args.avatar, args.upload, args.privacy, args.token)
    else:
        print("Interactive mode - processing sample script...")
        if not os.path.exists(args.avatar):
            print(f"\nAvatar not found: {args.avatar}")
            print(f"Place your avatar image at: {args.avatar}")
            print("Or specify: --avatar /path/to/image.png")
            
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (1920, 1080), color=(26, 26, 46))
            draw = ImageDraw.Draw(img)
            draw.text((960, 500), "INNERE STAERKE", fill=(233, 69, 96), anchor="mm")
            placeholder = os.path.join(TEMP_DIR, "placeholder_avatar.png")
            img.save(placeholder)
            args.avatar = placeholder
            print(f"Using placeholder: {placeholder}")
        
        result = process_single(SAMPLE_SCRIPTS[0], args.avatar, args.upload, args.privacy, args.token)
        if result:
            print(f"\nResult: {result}")


if __name__ == "__main__":
    main()
