# ProductPulse — Aspect-Based Sentiment Analysis Annotation Guidelines

> **Target Domain:** Mobile Phones & Accessories (`Cell_Phones_and_Accessories`)  
> **Source Corpus:** Official Amazon Reviews 2023 (`McAuley-Lab/Amazon-Reviews-2023`)  
> **Unit of Annotation:** Atomic pair `(sentence_id, aspect_name)` linked to verbatim text offsets.

---

## 1. Principles & Integrity Rules

1. **Evidence Grounding**: Annotate only what the customer explicitly wrote in the sentence. Do not extrapolate unmentioned features, assume product faults without statement, or use customer star ratings as sentiment ground truth.
2. **Three Decoupled States**:
   - `detection_status`: `present` vs `absent` (whether the sentence mentions this specific aspect).
   - `annotation_status`: `unannotated` vs `annotated` (whether a human has reviewed the record).
   - `sentiment_label`: `positive`, `neutral`, `negative`, or `uncertain/unclassified`.
   - **Crucial Rule**: If `detection_status == absent`, `sentiment_label` MUST be `None`. An absent aspect never receives a sentiment label.
3. **No Silent Discarding**: Ambiguous or mixed statements must be annotated as `uncertain/unclassified` with explanatory notes rather than discarded or forced into standard classes.
4. **Category Lock**: All annotations are strictly bounded to mobile phones and accessories.

---

## 2. Aspect Taxonomy Definitions

| Aspect Code | Aspect Name | Scope & Typical Components | Negative Example | Positive Example |
| :--- | :--- | :--- | :--- | :--- |
| `build_durability` | Build & Durability | Materials, casing, drop resistance, hinges, scratches, buttons, build quality. | *"The plastic back cracked after one small drop."* | *"Very sturdy aluminum frame, feels premium."* |
| `battery_charging` | Battery & Charging | Battery runtime, discharge rate, charging speed, cables, wireless charging, overheating while charging. | *"Battery drains in four hours even on standby."* | *"Fast charging gets me to 80% in 30 minutes."* |
| `screen_display` | Screen & Display | Brightness, resolution, OLED/LCD, touch response, refresh rate, glare, viewing angles. | *"The display is completely washed out in sunlight."* | *"Vibrant OLED screen with super smooth 120Hz."* |
| `camera_optics` | Camera & Optics | Photo quality, low-light/night mode, lenses, zoom, video stabilization, focus speed. | *"Pictures look grainy and blurry in low light."* | *"Takes crisp, sharp portraits with natural colors."* |
| `connectivity_audio` | Connectivity & Audio | Bluetooth pairing, Wi-Fi, 5G/cellular reception, speaker loudness, call clarity, microphone. | *"Bluetooth constantly disconnects while driving."* | *"Call clarity is excellent and speaker is very loud."* |
| `performance_software` | Performance & Software | Speed, UI smoothness, gaming lag, app crashes, OS updates, system freezes, RAM management. | *"The phone freezes frequently after the latest update."* | *"Snappy processor, no lag even with heavy multitasking."* |

---

## 3. Disambiguation Rules for Domain Terms

- **"Case"**:
  - If referring to a protective phone case $\implies$ `build_durability`.
  - If an idiomatic expression (*"in this case"*, *"just in case"*) $\implies$ NOT an aspect mention (`detection_status = absent`).
- **"Cord" / "Cable"**:
  - If referring to a charging cord $\implies$ `battery_charging`.
  - If referring to wired headphones $\implies$ `connectivity_audio`.
- **"Touch"**:
  - If referring to touchscreen responsiveness $\implies$ `screen_display`.
  - If referring to physical feel/finish $\implies$ `build_durability`.

---

## 4. Sentiment Label Criteria

1. **`positive`**: Customer expresses clear satisfaction, praise, or favorable performance regarding the specific aspect.
2. **`neutral`**: Customer states objective facts, physical specifications, or inquiries without subjective praise or criticism (*"This charger outputs 15 watts"*, *"It has a 6.5 inch screen"*).
3. **`negative`**: Customer expresses clear dissatisfaction, malfunction, defect, or disappointment regarding the specific aspect.
4. **`uncertain/unclassified`**: Use in the following explicit cases:
   - **Conflicting polarity within the same aspect in the same sentence**: *"The camera takes great photos during the day, but horrible ones at night."* (Mark `uncertain/unclassified` with note `mixed_aspect_sentiment`).
   - **Sarcasm or ambiguous irony**: *"Love how the battery dies right when I need GPS."*
   - **Insufficient evidence / Truncated sentence**: Meaning cannot be determined from the snippet alone.

---

## 5. Multiple Aspects in One Sentence

When a sentence mentions multiple aspects with different sentiments:
- Each aspect is evaluated as an **independent** `(sentence_id, aspect_name)` unit.
- *Example*: *"The screen is gorgeous but the battery life is terrible."*
  - `(sentence_id, screen_display)` $\implies$ `detection_status = present`, `sentiment_label = positive`.
  - `(sentence_id, battery_charging)` $\implies$ `detection_status = present`, `sentiment_label = negative`.
  - `(sentence_id, camera_optics)` $\implies$ `detection_status = absent`, `sentiment_label = None`.

---

## 6. Step-by-Step Annotation Walkthrough

For each unit in the evaluation template:
1. Read the `sentence_text` in context.
2. Decide if the specified `aspect_name` is mentioned:
   - If **NO**: Set `detection_status = "absent"`, leave `sentiment_label = None`, set `annotation_status = "annotated"`.
   - If **YES**: Set `detection_status = "present"`.
3. If `detection_status == "present"`, determine sentiment for this aspect:
   - Choose `positive`, `neutral`, `negative`, or `uncertain/unclassified`.
   - Set `annotation_status = "annotated"`.
4. If ambiguous, record the reason in the `notes` column.
