# 元にするフォントと Unicode のデータ。版とハッシュを固定し、ビルドの中ではネットワークに出ない。
# 版を上げるときは URL を変え、hash を lib.fakeHash にして一度ビルドし、出てきた値に差し替える。
{
  fetchurl,
  runCommand,
  linkFarm,
}:
let
  plex = "https://raw.githubusercontent.com/IBM/plex";
  mono = file: hash: {
    name = "mono/${file}";
    path = fetchurl {
      url = "${plex}/@ibm/plex-mono@2.5.0/packages/plex-mono/fonts/complete/ttf/${file}";
      inherit hash;
    };
  };
  jp = file: hash: {
    name = "jp/${file}";
    path = fetchurl {
      url = "${plex}/@ibm/plex-sans-jp@3.0.0/packages/plex-sans-jp/fonts/complete/ttf/unhinted/${file}";
      inherit hash;
    };
  };
  nerdFonts = runCommand "nerd-fonts-symbols-3.5.1" {
    src = fetchurl {
      url = "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.5.1/NerdFontsSymbolsOnly.tar.xz";
      hash = "sha256-ARcvN9uFQ+2xAuXLXGQQHJ9GhmMIBNSbQZqgeyOmmZY=";
    };
  } "mkdir $out && tar -xJf $src -C $out";
  ucd = file: url: hash: {
    name = file;
    path = fetchurl { inherit url hash; };
  };
  unicode = "https://www.unicode.org/Public/18.0.0";
in
{
  fonts = linkFarm "lievre-term-sources" [
    (mono "IBMPlexMono-Regular.ttf" "sha256-fG+93KS3AL6Rj19hg9m9RGT6Qn/kNfC0gNd/4ruMWkM=")
    (mono "IBMPlexMono-Medium.ttf" "sha256-mPvXJ6rjQLI2lVh52r7U2ZGqyejpCzsqZ85KWSIcyXw=")
    (mono "IBMPlexMono-SemiBold.ttf" "sha256-8E18SI3ffR+pnyV078NAbqTL4XuxrzoauWD4TQyWoXI=")
    (jp "IBMPlexSansJP-Regular.ttf" "sha256-AWhJOuFD0W5MDTdMCQse5eq57kdVNtLkKTaNvPxKar4=")
    (jp "IBMPlexSansJP-Medium.ttf" "sha256-7ZJXyUsKVAusVqD6pw7FVLGOpycfpPDTNRJYPdS/nAw=")
    (jp "IBMPlexSansJP-SemiBold.ttf" "sha256-OuF69zBikmsBOv3siUmSOorf1OyMT2iYdsCjWeY+TOs=")
    {
      name = "nf/SymbolsNerdFontMono-Regular.ttf";
      path = "${nerdFonts}/SymbolsNerdFontMono-Regular.ttf";
    }
  ];

  ucd = linkFarm "unicode-18.0.0-ucd" [
    (ucd "EastAsianWidth.txt" "${unicode}/ucd/EastAsianWidth.txt"
      "sha256-oM8p6s0Az8rsQ4HGt8KBaF8Y27Tn/4K0B2zLNCyoOao="
    )
    (ucd "DerivedGeneralCategory.txt" "${unicode}/ucd/extracted/DerivedGeneralCategory.txt"
      "sha256-1rFR0tQO6bGHbSb0F5gPRf+uR7YFXM9yA8sx8HoDD5Q="
    )
    (ucd "DerivedCoreProperties.txt" "${unicode}/ucd/DerivedCoreProperties.txt"
      "sha256-CckoiGoXj8r9k8KeS9WQc6BY5aEAtxbUJctWOrUPaMk="
    )
    (ucd "emoji-sequences.txt" "${unicode}/emoji/emoji-sequences.txt"
      "sha256-GCPc5x892csK0Zdnl7ruT/vcGQl1b0OvjOTFf3MoQ6Q="
    )
  ];
}
