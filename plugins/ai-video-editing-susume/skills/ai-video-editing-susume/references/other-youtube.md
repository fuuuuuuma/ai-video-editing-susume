# その他のYouTube：10本学習

指定チャンネルの同じ編集様式を持つ、異なる動画10本以上を実際に確認する。動画IDで重複除外し、転載、広告、別チャンネル、Shortsの切り抜きを無断で混ぜない。

## 選び方

- 指定期間があれば期間内だけを対象にする。
- 指定がなければ現行様式を中心に、今回に近い単独、対談、実演、比較等を含める。
- URL一覧、検索結果、タイトル、サムネイル、字幕、章の取得だけでは1本に数えない。

## 各動画で行うこと

1. 冒頭、通常説明、実演・図、強調、構成転換、終了を時間順に見る。
2. 少なくとも3場面を前後付きで深掘りする。
3. 各場面に`before / entry / hold / exit / caption_interaction / framing / audio_status`を記録する。
4. 音を採用する場面は実際に試聴し、SE、BGM、声、元動画の実音を分ける。
5. フォント、サイズ、色、縁、影、位置、倍率は確認方法と一緒に記録する。画面推定値とネイティブ値を混ぜない。

## `videos.json`

各動画に次を持たせる。

```json
{
  "id": "video-id",
  "channel_id": "channel-id",
  "title": "title",
  "url": "https://www.youtube.com/watch?v=...",
  "date": "20260901",
  "duration": 600.0,
  "visual_reviewed": true,
  "full_watch": false,
  "audio_reviewed": false,
  "temporal_reviews": [
    {
      "start": 10.0,
      "end": 14.0,
      "method": "video_playback",
      "evidence_ref": "local review note or permitted clip",
      "before": "normal state",
      "entry": "emphasis enters",
      "hold": "caption and frame stay",
      "exit": "returns to normal",
      "caption_interaction": "normal caption is replaced",
      "audio_status": "listened",
      "audio_notes": "SE starts with the emphasis"
    }
  ]
}
```

`full_watch`と`audio_reviewed`は実施した場合だけtrueにする。件数検査は映像を本当に見たこと、解釈、フォント一致、音量を保証しない。

## 編集への接続

10本の共通傾向と例外を分け、今回の主参照を1本選ぶ。通常字幕、強調、画面収録、図、ワイプ、SE、BGM、CTAについて「使う条件」「使わない条件」「入り・保持・戻り」を表にしてから編集へ進む。既知4チャンネルの見た目を代用しない。
