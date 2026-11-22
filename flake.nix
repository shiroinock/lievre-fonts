{
  description = "Lievre Term: lievre の端末用フォント（IBM Plex Mono と IBM Plex Sans JP を 1:2 に）";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachSystem [ "aarch64-darwin" "x86_64-linux" "aarch64-linux" ] (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        lib = pkgs.lib;
        py = pkgs.python313Packages; # 標準の Python 3.13（.python-version と同じ）
        sources = pkgs.callPackage ./nix/sources.nix { };

        src = lib.fileset.toSource {
          root = ./.;
          fileset = lib.fileset.unions [
            ./pyproject.toml
            ./src
            ./tests
          ];
        };

        # フォントを組み立てる道具。
        tool = py.buildPythonApplication {
          pname = "lievre-term-build";
          version = "0.1.0";
          pyproject = true;
          inherit src;
          build-system = [ py.setuptools ];
          dependencies = [
            py.fonttools
            py.brotli
          ];
          doCheck = false; # テストはフォントを組んだあと（checks.tests）で流す
          meta.mainProgram = "lievre-term-build";
        };

        variants = [
          "lievre-term"
          "lievre-term-nf"
          "lievre-term-jp1"
          "lievre-term-jp1-nf"
          "lievre-term-jp"
          "lievre-term-jp-nf"
        ];

        licenses = lib.fileset.toSource {
          root = ./.;
          fileset = ./LICENSES;
        };

        # 1つのバリエーションの 400 / 500 / 600 を、ttf と woff2、Web 用の分けた woff2 と CSS で。
        mkVariant =
          id:
          pkgs.stdenvNoCC.mkDerivation {
            pname = id;
            version = "0.1.0";
            dontUnpack = true;
            nativeBuildInputs = [ tool ];
            buildPhase = ''
              runHook preBuild
              lievre-term-build fonts --sources ${sources.fonts} --ucd ${sources.ucd} \
                --variant ${id} --out out
              runHook postBuild
            '';
            installPhase = ''
              runHook preInstall
              install -Dm644 -t $out/share/fonts/truetype out/ttf/*.ttf
              # woff2 は Web 用。share/fonts に置くと fontconfig が ttf と二重に拾うので、外に置く。
              install -Dm644 -t $out/share/lievre-term/woff2 out/woff2/*.woff2
              # Web 用：unicode-range で分けた woff2 と、そのまま読み込める @font-face の CSS。
              mkdir -p $out/share/lievre-term/web
              cp -r out/web/. $out/share/lievre-term/web/
              ln -s ../fonts/truetype $out/share/lievre-term/ttf
              cp -r ${licenses}/LICENSES $out/share/lievre-term/LICENSES
              ln -s ${widths}/share/lievre-term/widths.json $out/share/lievre-term/widths.json
              runHook postInstall
            '';
            meta = {
              description = "Lievre Term (${id})";
              license = lib.licenses.ofl;
              platforms = lib.platforms.all;
            };
          };

        # Lievre Sans（本文の書体）。Plex Sans JP の行の箱と名前だけを変えたもの。
        sans = pkgs.stdenvNoCC.mkDerivation {
          pname = "lievre-sans";
          version = "0.1.0";
          dontUnpack = true;
          nativeBuildInputs = [ tool ];
          buildPhase = ''
            runHook preBuild
            lievre-term-build sans --sources ${sources.fonts} --out out
            runHook postBuild
          '';
          installPhase = ''
            runHook preInstall
            install -Dm644 -t $out/share/fonts/truetype out/ttf/*.ttf
            install -Dm644 -t $out/share/lievre-term/woff2 out/woff2/*.woff2
            mkdir -p $out/share/lievre-term/web
            cp -r out/web/. $out/share/lievre-term/web/
            ln -s ../fonts/truetype $out/share/lievre-term/ttf
            cp -r ${licenses}/LICENSES $out/share/lievre-term/LICENSES
            runHook postInstall
          '';
          meta = {
            description = "Lievre Sans";
            license = lib.licenses.ofl;
            platforms = lib.platforms.all;
          };
        };

        # npm のパッケージ @lievre/fonts。Web で使う Lievre Sans・Lievre Term・Lievre Term JP の
        # 分けた woff2 と @font-face の CSS、幅の表、ライセンス。Releases に .tgz で載せる。
        npmPackage =
          let
            web = name: "${all}/share/lievre-term/web/${name}";
            packageJson = builtins.toJSON {
              name = "@lievre/fonts";
              version = "0.1.0";
              description = "lievre の書体（Lievre Sans・Lievre Term）の woff2 と @font-face";
              license = "OFL-1.1";
              repository = {
                type = "git";
                url = "git+https://github.com/shiroinock/lievre-fonts.git";
              };
              files = [
                "*.css"
                "files"
                "LICENSES"
                "widths.json"
              ];
              style = "fonts.css";
              sideEffects = [ "*.css" ];
              exports = {
                "." = "./fonts.css";
                "./fonts.css" = "./fonts.css";
                "./sans.css" = "./lievre-sans.css";
                "./term.css" = "./lievre-term.css";
                "./term-jp.css" = "./lievre-term-jp.css";
                "./widths.json" = "./widths.json";
                "./package.json" = "./package.json";
              };
            };
          in
          pkgs.runCommand "lievre-fonts-npm-0.1.0"
            {
              passAsFile = [ "packageJson" ];
              inherit packageJson;
            }
            ''
              p=package
              mkdir -p $p/files
              for id in lievre-sans lievre-term lievre-term-jp; do cp ${web "$id.css"} $p/; done
              for stem in LievreSans LievreTerm LievreTermJP; do cp ${web "files"}/"$stem"-*.woff2 $p/files/; done
              printf '@import "./lievre-sans.css";\n@import "./lievre-term-jp.css";\n' > $p/fonts.css
              cp $packageJsonPath $p/package.json
              cp ${./nix/npm-README.md} $p/README.md
              cp -r ${licenses}/LICENSES $p/LICENSES
              cp ${widths}/share/lievre-term/widths.json $p/widths.json
              chmod -R u+w $p
              mkdir -p $out/share/lievre-fonts
              cp -r $p $out/share/lievre-fonts/npm
              # 同じ中身なら同じ .tgz になるように、時刻と持ち主をそろえる。
              tar --sort=name --mtime=@1 --owner=0 --group=0 --numeric-owner -cf - $p | gzip -n > $out/lievre-fonts-0.1.0.tgz
            '';

        # 字の幅の表。@lievre/tui が読む。
        widths = pkgs.runCommand "lievre-term-widths" { nativeBuildInputs = [ tool ]; } ''
          lievre-term-build widths --ucd ${sources.ucd} --out $out/share/lievre-term/widths.json
        '';

        variantPackages = lib.genAttrs variants mkVariant;

        all = pkgs.symlinkJoin {
          name = "lievre-term-all";
          paths = builtins.attrValues variantPackages ++ [ sans ];
          postBuild = ''
            # 各バリエーションの ttf の張り方とライセンスは同じなので、まとめて張り直す。
            rm -rf $out/share/lievre-term/ttf $out/share/lievre-term/LICENSES $out/share/lievre-term/widths.json
            ln -s ../fonts/truetype $out/share/lievre-term/ttf
            cp -r ${licenses}/LICENSES $out/share/lievre-term/LICENSES
            ln -s ${widths}/share/lievre-term/widths.json $out/share/lievre-term/widths.json
          '';
        };

        python = pkgs.python313.withPackages (ps: [
          ps.fonttools
          ps.brotli
          ps.pytest
        ]);
      in
      {
        packages = variantPackages // {
          inherit tool widths all;
          lievre-sans = sans;
          npm = npmPackage;
          default = all;
        };

        apps.default = {
          type = "app";
          program = lib.getExe tool;
          meta.description = "Lievre Term を組み立てる";
        };

        checks = {
          tests =
            pkgs.runCommand "lievre-term-tests"
              {
                nativeBuildInputs = [ python ];
                LIEVRE_TERM_FONTS = "${all}/share/lievre-term";
                LIEVRE_TERM_UCD = "${sources.ucd}";
              }
              ''
                cp -r ${src}/. work && chmod -R u+w work && cd work
                PYTHONPATH=src python -m pytest -q -p no:cacheprovider
                touch $out
              '';
          format =
            pkgs.runCommand "lievre-term-format"
              {
                nativeBuildInputs = [
                  pkgs.ruff
                  pkgs.nixfmt
                ];
              }
              ''
                cd ${self}
                ruff format --no-cache --check src tests
                ruff check --no-cache src tests
                nixfmt --check flake.nix nix/*.nix
                touch $out
              '';
        };

        devShells.default = pkgs.mkShell {
          packages = [
            python
            pkgs.ruff
            pkgs.nixfmt
            pkgs.uv
          ];
          shellHook = ''
            export PYTHONPATH="$PWD/src''${PYTHONPATH:+:$PYTHONPATH}"
            export LIEVRE_TERM_SOURCES=${sources.fonts}
            export LIEVRE_TERM_UCD=${sources.ucd}
          '';
        };

        formatter = pkgs.writeShellApplication {
          name = "lievre-term-format";
          runtimeInputs = [
            pkgs.ruff
            pkgs.nixfmt
          ];
          text = ''
            ruff format src tests
            ruff check --fix src tests
            nixfmt flake.nix nix/*.nix
          '';
        };
      }
    );
}
