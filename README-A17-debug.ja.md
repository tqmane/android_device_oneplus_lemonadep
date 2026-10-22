# OnePlus 9 Pro / Android 17 診断用TWRP

2026-10-23。実機で使用した診断用Recoveryの設定をこのデバイスツリーへ反映した。
通常のAndroid 17用TWRPのFBE復号対応が完了した、という意味ではない。

## /dataが読めなかった原因

旧RecoveryカーネルのF2FSはOplus拡張inodeに未対応で、実際のextra_isize=48を
上限36として拒否し、EUCLEANを返した。通常起動側の対応カーネルへ交換すると
同じfilesystemを読み取りできた。これを根拠に破損と判断したり、Format Dataや
fsckの修復書き込みを実行したりする必要はなかった。

これとは別に、古いqcom_decrypt/keymasterによる自動復号とRecovery GUIの自動開始を
止め、ADBから手動で診断した。過去の確認は/dataのro,norecovery、/metadataの
ro,noload読み取りとtombstone採取であり、ロック画面認証付きCEデータの復号までを
確認したものではない。EROFSの新しい圧縮機能にも対応するカーネルが必要だった。
USBのVMへの再接続問題は、このF2FSエラーとは別問題。

## 反映した内容

- 通常共通ツリーの古いImageではなく、実機で診断に使用したImageを選択する。
- 対応する18個のモジュール／関連ファイルを元の診断ramdiskから保存する。
- 自動qcom_decryptのimportとパッケージを外し、cryptoビルド設定をfalseにする。
- fstabから/dataと/metadataの自動処理を外す。パーティションや暗号鍵を消去しない。
- recoveryサービスはdisabledで開始する。必要な場合はADBから `start recovery`。
- 動作済み画像と同様に、VINTFファイルを削除する起動時スクリプトを呼ばない。

元のtwrp.flagsの手動操作用項目は残すが、それによってA17の復号が可能になるわけではない。
データのマウント可否・mapper・暗号状態は実機で確認してから扱うこと。

## 保存先・再ビルド

動作済み画像: `/home/tqmane/git/OTA/OnePlus9Pro-TWRP-A17-debug.img`

この画像はRAM起動によるデバッグ用。今回の作業で端末へのフラッシュは行っていない。
ロック解除済みの対象LE2120を確認してから一時起動する。

```sh
fastboot boot /home/tqmane/git/OTA/OnePlus9Pro-TWRP-A17-debug.img
```

`prebuilt/Image` と `prebuilt/modules/` は、この画像のkernelと
ramdisk内vendor/lib/modules/1.1を取り出して配置済み。端末固有情報は含まないが、
約50MBのカーネル等を無条件に公開しないためローカル専用としてGitから除外する。
別環境では保存画像をmagiskbootでunpackし、同じ2か所へ配置する必要がある。
元画像のkernelとmodulesを組で使い、別ビルドのものを無条件に混ぜない。

TWRPのandroid-12.1ビルド環境内でdevice/oneplus/lemonadepに置き、
twrp.dependenciesのsm8350-commonも用意して通常どおりビルドする。
このディレクトリ単独にはTWRP本体と共通ツリーがないため、今回はフルビルドしていない。

```sh
python3 -m unittest discover -s tests -v
```

設定・prebuiltの構造検査と、元画像から取り出したkernel/modulesのバイト一致を確認した。
保存した画像は以前の実機動作済み画像そのもの。更新後ツリーを新規ビルドした画像の
起動・マウント・復号は未検証。
