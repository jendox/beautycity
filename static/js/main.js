$(document).ready(function() {
	$('.salonsSlider').slick({
		arrows: true,
	  slidesToShow: 4,
	  infinite: true,
	  prevArrow: $('.salons .leftArrow'),
	  nextArrow: $('.salons .rightArrow'),
	  responsive: [
	    {
	      breakpoint: 991,
	      settings: {
	        
	      	centerMode: true,
  			//centerPadding: '60px',
	        slidesToShow: 2
	      }
	    },
	    {
	      breakpoint: 575,
	      settings: {
	        slidesToShow: 1
	      }
	    }
	  ]
	});
	$('.servicesSlider').slick({
		arrows: true,
	  slidesToShow: 4,
	  prevArrow: $('.services .leftArrow'),
	  nextArrow: $('.services .rightArrow'),
	  responsive: [
	  	{
	      breakpoint: 1199,
	      settings: {
	        

	        slidesToShow: 3
	      }
	    },
	    {
	      breakpoint: 991,
	      settings: {
	        
	      	centerMode: true,
  			//centerPadding: '60px',
	        slidesToShow: 2
	      }
	    },
	    {
	      breakpoint: 575,
	      settings: {
	        slidesToShow: 1
	      }
	    }
	  ]
	});

	$('.mastersSlider').slick({
		arrows: true,
	  slidesToShow: 4,
	  prevArrow: $('.masters .leftArrow'),
	  nextArrow: $('.masters .rightArrow'),
	  responsive: [
	  	{
	      breakpoint: 1199,
	      settings: {
	        

	        slidesToShow: 3
	      }
	    },
	    {
	      breakpoint: 991,
	      settings: {
	        

	        slidesToShow: 2
	      }
	    },
	    {
	      breakpoint: 575,
	      settings: {
	        slidesToShow: 1
	      }
	    }
	  ]
	});

	$('.reviewsSlider').slick({
		arrows: true,
	  slidesToShow: 4,
	  prevArrow: $('.reviews .leftArrow'),
	  nextArrow: $('.reviews .rightArrow'),
	  responsive: [
	  	{
	      breakpoint: 1199,
	      settings: {
	        

	        slidesToShow: 3
	      }
	    },
	    {
	      breakpoint: 991,
	      settings: {
	        

	        slidesToShow: 2
	      }
	    },
	    {
	      breakpoint: 575,
	      settings: {
	        slidesToShow: 1
	      }
	    }
	  ]
	});

	// menu
	$('.header__mobMenu').click(function() {
		$('#mobMenu').show()
	})
	$('.mobMenuClose').click(function() {
		$('#mobMenu').hide()
	})

	if (document.querySelector('#datepickerHere')) {
		new AirDatepicker('#datepickerHere')
	}

	$(document).on('click', '.accordion', function(e) {
		e.preventDefault()
		$(this).toggleClass('active')
		$(this).next().toggleClass('active')
	})

	function escapeHtml(value) {
		return String(value ?? '').replace(/[&<>"']/g, function(match) {
			switch (match) {
				case '&': return '&amp;'
				case '<': return '&lt;'
				case '>': return '&gt;'
				case '"': return '&quot;'
				case "'": return '&#39;'
				default: return match
			}
		})
	}

	function formatRuble(value) {
		const amount = Number(value || 0)
		try {
			return new Intl.NumberFormat('ru-RU').format(amount) + ' ₽'
		} catch (e) {
			return String(amount) + ' ₽'
		}
	}

	const STATIC_URL = (window.BEAUTYCITY_STATIC_URL || '/static/').replace(/\/?$/, '/')

	function staticPath(path) {
		return STATIC_URL + String(path || '').replace(/^\//, '')
	}

	function isServicePage() {
		return $('.servicePage').length && $('.service__form').length
	}

	function closeAccordion($button) {
		$button.removeClass('active')
		$button.next().removeClass('active')
	}

	async function fetchJson(url) {
		const res = await fetch(url, {method: 'GET', credentials: 'include'})
		let data = null
		try { data = await res.json() } catch (e) {}
		if (!res.ok) {
			throw new Error('request_failed')
		}
		return data
	}

	function renderSalons(salons) {
		if (!Array.isArray(salons) || !salons.length) {
			return '<div class="accordion__block fic"><div class="accordion__block_intro">Нет доступных салонов</div></div>'
		}
		return salons.map(function(salon) {
			const name = escapeHtml(salon.name)
			const address = escapeHtml(salon.address || '')
			return (
				'<div class="accordion__block fic" data-salon-id="' + escapeHtml(salon.id) + '">' +
					'<div class="accordion__block_intro">' + name + '</div>' +
					'<div class="accordion__block_address">' + address + '</div>' +
				'</div>'
			)
		}).join('')
	}

	function renderServicesByCategories(data) {
		if (!data || (!Array.isArray(data.categories) && !Array.isArray(data.uncategorized))) {
			return '<div class="accordion__block fic"><div class="accordion__block_intro">Не удалось загрузить услуги</div></div>'
		}

		const parts = []
		const categories = Array.isArray(data.categories) ? data.categories : []
		const uncategorized = Array.isArray(data.uncategorized) ? data.uncategorized : []

		function renderServiceItem(service) {
			const title = escapeHtml(service.title)
			const price = formatRuble(service.price)
			return (
				'<div class="accordion__block_item fic" data-service-id="' + escapeHtml(service.id) + '">' +
					'<div class="accordion__block_item_intro">' + title + '</div>' +
					'<div class="accordion__block_item_address">' + escapeHtml(price) + '</div>' +
				'</div>'
			)
		}

		categories.forEach(function(category) {
			const services = Array.isArray(category.services) ? category.services : []
			if (!services.length) return

			parts.push('<button class="accordion">' + escapeHtml(category.title) + '</button>')
			parts.push(
				'<div class="panel">' +
					'<div class="accordion__block_items">' +
						services.map(renderServiceItem).join('') +
					'</div>' +
				'</div>'
			)
		})

		if (uncategorized.length) {
			parts.push('<button class="accordion">Другое</button>')
			parts.push(
				'<div class="panel">' +
					'<div class="accordion__block_items">' +
						uncategorized.map(renderServiceItem).join('') +
					'</div>' +
				'</div>'
			)
		}

		if (!parts.length) {
			return '<div class="accordion__block fic"><div class="accordion__block_intro">Услуг нет</div></div>'
		}

		return parts.join('')
	}

	function renderMasters(masters) {
		const rows = []

		rows.push(
			'<div class="accordion__block fic" data-master-id="">' +
				'<div class="accordion__block_elems fic">' +
					'<img src="' + escapeHtml(staticPath('img/masters/avatar/all.svg')) + '" alt="avatar" class="accordion__block_img">' +
					'<div class="accordion__block_master">Любой мастер</div>' +
				'</div>' +
			'</div>'
		)

		if (Array.isArray(masters)) {
			masters.forEach(function(master) {
				const imgSrc = master.image_url ? String(master.image_url) : staticPath('img/masters/avatar/vizajist1.svg')
				rows.push(
					'<div class="accordion__block fic" data-master-id="' + escapeHtml(master.id) + '">' +
						'<div class="accordion__block_elems fic">' +
							'<img src="' + escapeHtml(imgSrc) + '" onerror="this.onerror=null;this.src=\'' + escapeHtml(staticPath('img/masters/avatar/vizajist1.svg')) + '\'" alt="avatar" class="accordion__block_img">' +
							'<div class="accordion__block_master">' + escapeHtml(master.name) + '</div>' +
						'</div>' +
					'</div>'
				)
			})
		}

		return rows.join('')
	}

	function resetServiceSelection() {
		const $button = $('.service__services > button.accordion')
		$button.removeClass('selected').text('(Выберите услугу)')
	}

	function resetMasterSelection() {
		const $button = $('.service__masters > button.accordion')
		$button.removeClass('selected').text('(Выберите мастера)')
	}

	function updateNextButton() {
		if (!isServicePage()) return

		const hasTime = $('.time__items .time__elems_elem .time__elems_btn.active').length > 0
		const hasSalon = $('.service__salons > button.accordion').hasClass('selected')
		const hasService = $('.service__services > button.accordion').hasClass('selected')
		const hasMaster = $('.service__masters > button.accordion').hasClass('selected')

		if (hasTime && hasSalon && hasService && hasMaster) {
			$('.time__btns_next').addClass('active')
		} else {
			$('.time__btns_next').removeClass('active')
		}
	}

	async function initServiceCatalog() {
		if (!isServicePage()) return

		const $salonPanel = $('.service__salons > .panel')
		const $servicesPanel = $('.service__services > .panel')
		const $mastersPanel = $('.service__masters > .panel')
		const $form = $('.service__form')

		$salonPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Загрузка...</div></div>')
		try {
			const salonsPayload = await fetchJson('/api/salons/')
			$salonPanel.html(renderSalons(salonsPayload && salonsPayload.results))
		} catch (e) {
			$salonPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Не удалось загрузить салоны</div></div>')
		}

		$(document).on('click', '.service__salons > .panel .accordion__block', async function(e) {
			e.preventDefault()

			const $row = $(this)
			const salonId = $row.attr('data-salon-id')
			const name = $row.find('> .accordion__block_intro').text()
			const address = $row.find('> .accordion__block_address').text()

			const $salonButton = $row.closest('.service__salons').find('> button.accordion')
			$salonButton.addClass('selected').text(name + (address ? '  ' + address : ''))
			closeAccordion($salonButton)

			$form.attr('data-salon-id', salonId || '')
			$form.attr('data-service-id', '')
			$form.attr('data-master-id', '')

			resetServiceSelection()
			resetMasterSelection()

			$servicesPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Загрузка...</div></div>')
			$mastersPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Загрузка...</div></div>')

			try {
				const payloads = await Promise.all([
					fetchJson('/api/salons/' + encodeURIComponent(salonId) + '/services/'),
					fetchJson('/api/salons/' + encodeURIComponent(salonId) + '/masters/'),
				])
				$servicesPanel.html(renderServicesByCategories(payloads[0]))
				$mastersPanel.html(renderMasters(payloads[1] && payloads[1].results))
			} catch (err) {
				$servicesPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Не удалось загрузить услуги</div></div>')
				$mastersPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Не удалось загрузить мастеров</div></div>')
			}

			updateNextButton()
		})

		$(document).on('click', '.service__services > .panel .accordion__block_item', function(e) {
			e.preventDefault()

			const $item = $(this)
			const serviceId = $item.attr('data-service-id')
			const title = $item.find('> .accordion__block_item_intro').text()
			const price = $item.find('> .accordion__block_item_address').text()

			const $servicesButton = $item.closest('.service__services').find('> button.accordion')
			$servicesButton.addClass('selected').text(title + (price ? '  ' + price : ''))
			closeAccordion($servicesButton)

			$form.attr('data-service-id', serviceId || '')
			updateNextButton()
		})

		$(document).on('click', '.service__masters > .panel .accordion__block', function(e) {
			e.preventDefault()

			const $row = $(this)
			const masterId = $row.attr('data-master-id')

			const $mastersButton = $row.closest('.service__masters').find('> button.accordion')
			$mastersButton.addClass('selected').html($row.clone())
			closeAccordion($mastersButton)

			$form.attr('data-master-id', masterId || '')
			updateNextButton()
		})

		updateNextButton()
	}

	initServiceCatalog()



	// 	console.log($('.service__masters > .panel').attr('data-masters'))
	// if($('.service__salons .accordion.selected').text() === "BeautyCity Пушкинская  ул. Пушкинская, д. 78А") {
	// }


	$(document).on('click', '.servicePage', function() {
		updateNextButton()
	})

	// $('.accordion__block_item').click(function(e) {
	// 	const thisName = $(this).find('.accordion__block_item_intro').text()
	// 	const thisAddress = $(this).find('.accordion__block_item_address').text()
	// 	console.log($(this).parent().parent().parent().parent())
	// 	$(this).parent().parent().parent().parent().find('button.active').addClass('selected').text(thisName + '  ' +thisAddress)
	// })



	// $('.accordion__block_item').click(function(e) {
	// 	const thisChildName = $(this).text()
	// 	console.log(thisChildName)
	// 	console.log($(this).parent().parent().parent())
	// 	$(this).parent().parent().parent().parent().parent().find('button.active').addClass('selected').text(thisChildName)

	// })
	// $('.accordion.selected').click(function() {
	// 	$(this).parent().find('.panel').hasClass('selected') ? 
	// 	 $(this).parent().find('.panel').removeClass('selected')
	// 		:
	// 	$(this).parent().find('.panel').addClass('selected')
	// })


	//popup
	$('.header__block_auth').click(function(e) {
		e.preventDefault()
		$('#authModal').arcticmodal();
		// $('#confirmModal').arcticmodal();

	})

	$('.rewiewPopupOpen').click(function(e) {
		e.preventDefault()
		$('#reviewModal').arcticmodal();
	})
	$('.payPopupOpen').click(function(e) {
		e.preventDefault()
		$('#paymentModal').arcticmodal();
	})
	$('.tipsPopupOpen').click(function(e) {
		e.preventDefault()
		$('#tipsModal').arcticmodal();
	})
	
//	$('.authPopup__form').submit(function() {
//		$('#confirmModal').arcticmodal();
//		return false
//	})

	//service
	$('.time__items .time__elems_elem .time__elems_btn').click(function(e) {
		e.preventDefault()
		$('.time__elems_btn').removeClass('active')
		$(this).addClass('active')
		updateNextButton()
		// $(this).hasClass('active') ? $(this).removeClass('active') : $(this).addClass('active')
	})

	$('.time__btns_next').click(function(e) {
		if (!$(this).hasClass('active')) {
			e.preventDefault()
			return
		}
		window.location.href = '/service/confirm/'
	})

	// OTP Auth
	function getCookie(name) {
		const m = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
		return m ? decodeURIComponent(m[2]) : null;
	}

	function ensureCsrf() {
		return fetch('/api/auth/csrf/', {credentials: 'include'});
	}

	function apiPost(url, payload) {
		const csrf = getCookie('csrftoken') || '';
		return fetch(url, {
			method: 'POST',
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrf,
			},
			body: JSON.stringify(payload || {}),
		}).then(async (res) => {
			let data = null;
			try { data = await res.json(); } catch (e) {}
			if (!res.ok) {
				const detail = data && (data.detail || data.non_field_errors || data.phone || data.code);
				const err = Array.isArray(detail) ? detail[0] : (detail || 'unknown_error');
				const error = new Error(err);
				error.status = res.status;
				error.data = data;
				throw error;
			}
			return data;
		});
	}

	function apiGet(url) {
		return fetch(url, {
			method: 'GET',
			credentials: 'include',
		}).then(async (res) => {
			let data = null;
			try { data = await res.json(); } catch (e) {}
			if (!res.ok) {
				const detail = data && (data.detail || data.non_field_errors);
				const err = Array.isArray(detail) ? detail[0] : (detail || 'unknown_error');
				const error = new Error(err);
				error.status = res.status;
				error.data = data;
				throw error;
			}
			return data;
		});
	}

	function mapAuthError(err) {
		switch (err.message) {
			case 'try_later': return 'Код уже отправлен. Подождите и попробуйте снова.';
			case 'invalid_phone': return 'Неверный формат номера телефона.';
			case 'phone_mismatch': return 'Номер не совпадает. Запросите код заново.';
			case 'code_expired': return 'Код истёк. Запросите новый.';
			case 'invalid_code': return 'Неверный код. Попробуйте ещё раз.';
			case 'too_many_attempts': return 'Слишком много попыток. Запросите новый код.';
			default: return 'Ошибка. Попробуйте ещё раз.';
  		}
	}

	let currentPhone = '';

	function showBlockError($el, text) {
		if (!$el || !$el.length) return;
		$el.text(text).show();
	}
	function hideBlockError($el) {
		if (!$el || !$el.length) return;
  		$el.text('').hide();
	}

	$('.authPopup__form').off('submit');

	// OTP Request
	$('.authPopup__form').on('submit', async function (e) {
		e.preventDefault();

		const $form = $(this);
		const $phoneInput = $form.find('input[name="tel"]');
		const phone = ($phoneInput.val() || '').trim();

		const $consent = $form.find('input[type="checkbox"]');
		const consentChecked = !$consent.length || $consent.is(':checked');
		if (!phone) {
			alert('Введите номер телефона.');
			return;
		}
		try {
			if (!consentChecked) {
				const status = await apiGet('/api/pd/consent-required/?phone=' + encodeURIComponent(phone));
				if (status && status.required) {
					alert('Нужно согласиться с политикой конфиденциальности.');
					return;
				}
			}
			await ensureCsrf();
			if (consentChecked) {
				await apiPost('/api/pd/consent/', { phone: phone, accepted: true });
			}
			await apiPost('/api/auth/request-code/', { phone });

			currentPhone = phone;

			$('#confirmPhoneText').text(phone);

			$.arcticmodal('close');
			$('#confirmModal').arcticmodal();

			const $inputs = $('#confirmModal').find('.confirmPopup__number input');
			$inputs.val('');
			$inputs.first().focus();

			hideBlockError($('#confirmError'));
		} catch (err) {
			showBlockError($('#authError'), mapAuthError(err));
			if (!$('#authError').length) alert(mapAuthError(err));
		}
	});

	// Input & Verify OTP
	(function setupOtpInputs() {
		const $wrap = $('#confirmModal').find('.confirmPopup__number');
		if (!$wrap.length) return;

		const $inputs = $wrap.find('input');

		function readCode() {
			let code = '';
			$inputs.each(function () { code += ($(this).val() || '').trim(); });
			return code;
		}

		function clearAndFocus() {
			$inputs.val('');
			$inputs.first().focus();
		}

		$inputs.attr('maxlength', '1');

		$inputs.on('input', async function () {
			hideBlockError($('#confirmError'));

			this.value = (this.value || '').replace(/\D/g, '').slice(0, 1);

			const idx = $inputs.index(this);
			if (this.value && idx < $inputs.length - 1) {
				$inputs.eq(idx + 1).focus();
			}

			const code = readCode();
			if (code.length === 4) {
				try {
					await ensureCsrf();
					const data = await apiPost('/api/auth/verify-code/', { phone: currentPhone, code });

					$.arcticmodal('close');
					if (data.next_url) {
						window.location.href = data.next_url;
					} else {
						window.location.reload();
					}
				} catch (err) {
					showBlockError($('#confirmError'), mapAuthError(err));
					clearAndFocus();
				}
			}
		});

		$inputs.on('keydown', function (ev) {
			if (ev.key === 'Backspace' && !this.value) {
				const idx = $inputs.index(this);
				if (idx > 0) $inputs.eq(idx - 1).focus();
			}
		});

		$(document).off('click', '#otpResendLink').on('click', '#otpResendLink', async function (e) {
    		e.preventDefault();
    		hideBlockError($('#confirmError'));

    		if (!currentPhone) {
      			showBlockError($('#confirmError'), 'Сначала введите номер телефона.');
      			return;
    		}

    		try {
      			await ensureCsrf();
      			await apiPost('/api/auth/request-code/', { phone: currentPhone });
      			clearAndFocus();
    		} catch (err) {
      			showBlockError($('#confirmError'), mapAuthError(err));
    		}
  		});

		$(document).off('click', '#otpChangePhoneLink').on('click', '#otpChangePhoneLink', function (e) {
    		e.preventDefault();
			hideBlockError($('#confirmError'));
    		clearAndFocus();
    		$.arcticmodal('close');
    		$('#authModal').arcticmodal();
  		});
	})();

	// Logout
	$(document).off('click', '.accaunt__settings_out').on('click', '.accaunt__settings_out', async function (e) {
		e.preventDefault();

		try {
			await ensureCsrf();
			await apiPost('/api/auth/logout/', {});
			window.location.href = '/';
		} catch (err) {
			alert('Не удалось выйти. Попробуйте ещё раз.');
		}
	});

	// ===== Auto-open auth modal if redirected with ?next=... =====
	(function () {
		const url = new URL(window.location.href);
		const next = url.searchParams.get('next');
		if (!next) return;

		url.searchParams.delete('next');
		window.history.replaceState({}, '', url.toString());

		if (window.jQuery && $('#authModal').length) {
			$('#authModal').arcticmodal();
		}
	})();

})
