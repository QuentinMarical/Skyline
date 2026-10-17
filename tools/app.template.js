/* Skyline Blocks - extension Mobirise : galerie de blocs prêts à l'emploi.
   Ce fichier est GÉNÉRÉ par tools/build_extension.py à partir de tools/app.template.js et de blocks/ : ne pas le modifier à la main. */
defineM("skyline-blocks", function(jQuery, mbrApp, TR) {

	var VERSION = "__VERSION__";
	var GROUPS = __GROUPS__;
	var BLOCKS = __BLOCKS__;

	// Clé du bloc sélectionné dans la galerie
	var selected = "";

	mbrApp.regExtension({
		name: "skyline-blocks",
		events: {
			load: function() {
				var a = this;

				// Les anciens thèmes (type "primary") n'utilisent pas le format de blocs personnalisés
				if (mbrApp.theme.type === "primary")
					return false;

				// Bouton dans la barre de navigation, à côté des icônes d'appareils
				a.$body.find(".navbar-devices").append('<li class="btnSkylineBlocks" style="width:66px; height:58px; cursor:pointer" data-tooltipster="bottom" title="Skyline Blocks"><i class="mbr-icon-cubes mbr-icon-image-gallery mbr-iconfont mbr-icon-photo mbr-icon-image"></i></li>');

				a.$body.on("click", ".btnSkylineBlocks", function() {
					// Restaure la vue bureau (pour que le menu des blocs continue de fonctionner)
					jQuery(".navbar-devices > li[data-device='desktop'] > a").trigger("click");
					selected = "";
					showGallery();
				});

				// Sélection d'un bloc dans la galerie
				a.$body.on("click", ".skyline-gallery-item", function() {
					selected = jQuery(this).data("block");
					jQuery(".skyline-gallery-item").removeClass("skyline-selected");
					jQuery(this).addClass("skyline-selected");
				});

				function esc(s) {
					return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
				}

				function galleryHTML() {
					var html = "";
					GROUPS.forEach(function(group) {
						var items = Object.keys(BLOCKS).filter(function(k) { return BLOCKS[k].group === group; });
						if (!items.length)
							return;
						html += '<h4 class="skyline-group">' + esc(group) + '</h4><div class="skyline-grid">';
						items.forEach(function(k) {
							html += '<div class="skyline-gallery-item" data-block="' + esc(k) + '" title="' + esc(BLOCKS[k].title) + '">' +
								'<img src="' + BLOCKS[k].thumb + '" alt="' + esc(BLOCKS[k].title) + '">' +
								'<span>' + esc(BLOCKS[k].title) + '</span></div>';
						});
						html += '</div>';
					});
					return html;
				}

				function showGallery() {
					var css = '<style>' +
						'.skyline-gallery-modal .modal-dialog { width: 80%; }' +
						'.skyline-scroll { height: ' + Math.ceil(window.innerHeight * 0.55) + 'px; overflow-y: auto; padding-right: 8px; }' +
						'.skyline-group { margin: 18px 0 8px; font-weight: 700; }' +
						'.skyline-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 12px; }' +
						'.skyline-gallery-item { cursor: pointer; border: 2px solid #e5e5e5; border-radius: 8px; overflow: hidden; background: #fff; }' +
						'.skyline-gallery-item:hover { border-color: #38bdf5; }' +
						'.skyline-gallery-item.skyline-selected { border-color: #080866; box-shadow: 0 0 0 2px #080866; }' +
						'.skyline-gallery-item img { display: block; width: 100%; height: 120px; object-fit: cover; object-position: top; }' +
						'.skyline-gallery-item span { display: block; padding: 6px 10px; font-size: 13px; }' +
						'</style>';

					mbrApp.showDialog({
						title: "Skyline Blocks",
						className: "skyline-gallery-modal",
						body: [css, '<div class="skyline-scroll">', galleryHTML(), '</div>'].join("\n"),
						buttons: [
							{
								label: "CANCEL",
								default: !1,
								callback: function() {}
							},
							{
								label: "ADD BLOCK TO PAGE",
								default: !0,
								callback: function() {
									if (!selected || !BLOCKS[selected]) {
										mbrApp.alertDlg("Please select a block.");
										return false;
									}
									try {
										importBlock(BLOCKS[selected]);
									}
									catch (err) {
										mbrApp.alertDlg(err.name + ", " + err.message);
									}
								}
							}
						]
					});
				}

				// Ajoute le bloc à la page courante, puis enregistre et recharge le projet
				function importBlock(block) {
					var cid = generateCID();
					var newBlock = {
						"alias":            false,
						"_styles":          JSON.parse(JSON.stringify(block.styles)),
						"_name":            "design-block",
						"_customHTML":      block.html,
						"_cid":             cid,
						"_protectedParams": [],
						"_global":          false,
						"_once":            false,
						"_params":          {},
						"_anchor":          "skyline-" + cid
					};

					var currentPage = mbrApp.Core.currentPage;
					var components = mbrApp.Core.resultJSON[currentPage].components;
					components[components.length] = newBlock;

					mbrApp.runSaveProject(function() {
						mbrApp.loadRecentProject(function() {
							jQuery("a[data-page='" + currentPage + "']").trigger("click");
						});
					});
				}

				// Génère un identifiant de composant unique dans tout le projet
				function generateCID() {
					var chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
					var pages = mbrApp.Core.getPages();
					var cid;
					var taken = true;
					while (taken) {
						cid = "";
						for (var i = 0; i < 10; i++)
							cid += chars.charAt(Math.floor(Math.random() * chars.length));
						taken = false;
						for (var page in pages) {
							for (var j = 0; j < pages[page]["components"].length; j++) {
								if (pages[page]["components"][j]["_cid"] === cid) {
									taken = true;
									break;
								}
							}
							if (taken)
								break;
						}
					}
					return cid;
				}
			}
		}
	});
}, ["jQuery", "mbrApp", "TR()"]);
