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

		// Datepicker for /service/ is initialized inside initServiceCatalog()

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
			const blocks = []
			blocks.push(
				'<div class="accordion__block fic" data-action="master-first">' +
					'<div class="accordion__block_intro">Мне не важно в какой салон</div>' +
					'<div class="accordion__block_address">Хочу к любимому мастеру</div>' +
				'</div>'
			)
			blocks.push(salons.map(function(salon) {
				const name = escapeHtml(salon.name)
				const address = escapeHtml(salon.address || '')
				return (
					'<div class="accordion__block fic" data-salon-id="' + escapeHtml(salon.id) + '">' +
						'<div class="accordion__block_intro">' + name + '</div>' +
						'<div class="accordion__block_address">' + address + '</div>' +
					'</div>'
				)
			}).join(''))
			return blocks.join('')
		}

		function renderMastersGlobal(masters) {
			if (!Array.isArray(masters) || !masters.length) {
				return '<div class="accordion__block fic"><div class="accordion__block_intro">Нет доступных мастеров</div></div>'
			}
			return masters.map(function(master) {
				const imgSrc = master.image_url ? String(master.image_url) : staticPath('img/masters/avatar/vizajist1.svg')
				const primarySalon = master.primary_salon || null
				const primarySalonId = primarySalon && primarySalon.id ? String(primarySalon.id) : ''
				const primarySalonName = primarySalon && primarySalon.name ? String(primarySalon.name) : ''
				return (
					'<div class="accordion__block fic" data-master-id="' + escapeHtml(master.id) + '" data-primary-salon-id="' + escapeHtml(primarySalonId) + '">' +
						'<div class="accordion__block_elems fic">' +
							'<img src="' + escapeHtml(imgSrc) + '" onerror="this.onerror=null;this.src=\'' + escapeHtml(staticPath('img/masters/avatar/vizajist1.svg')) + '\'" alt="avatar" class="accordion__block_img">' +
							'<div class="accordion__block_master">' + escapeHtml(master.name) + '</div>' +
						'</div>' +
						(primarySalonName ? '<div class="accordion__block_prof">' + escapeHtml(primarySalonName) + '</div>' : '') +
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
			const hasDate = Boolean($('.service__form').attr('data-date'))
			const hasTime = $('.time__items .time__elems_elem .time__elems_btn.active').length > 0 && Boolean($('.service__form').attr('data-time'))
			const hasSalon = $('.service__salons > button.accordion').hasClass('selected')
			const hasService = $('.service__services > button.accordion').hasClass('selected')
			const hasMaster = $('.service__masters > button.accordion').hasClass('selected')

			if (hasDate && hasTime && hasSalon && hasService && hasMaster) {
				$('.time__btns_next').addClass('active')
			} else {
				$('.time__btns_next').removeClass('active')
			}
		}

		async function initServiceCatalog() {
			if (!isServicePage()) return
			try { await ensureCsrf() } catch (e) {}

		const $salonPanel = $('.service__salons > .panel')
		const $servicesPanel = $('.service__services > .panel')
		const $mastersPanel = $('.service__masters > .panel')
		const $form = $('.service__form')
		const $slotsMorning = $('[data-role="slots-morning"]')
		const $slotsDay = $('[data-role="slots-day"]')
		const $slotsEvening = $('[data-role="slots-evening"]')
		const $slotsEmpty = $('[data-role="slots-empty"]')

			let availableDates = new Set()
			let datepicker = null
			const preSalonId = getQueryParam('salon_id')
			const preMasterId = getQueryParam('master_id')

		function pad2(n) {
			return String(n).padStart(2, '0')
		}

		function formatYmd(dateObj) {
			const d = new Date(dateObj.getTime())
			return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate())
		}

		function parseYmd(value) {
			const parts = String(value || '').split('-').map(Number)
			if (parts.length !== 3) return null
			const year = parts[0]
			const month = parts[1]
			const day = parts[2]
			if (!year || !month || !day) return null
			return new Date(year, month - 1, day)
		}

		function clearSlots() {
			$slotsMorning.empty()
			$slotsDay.empty()
			$slotsEvening.empty()
			$('.time__elems_btn').removeClass('active')
			$form.attr('data-time', '')
			$form.attr('data-starts-at', '')
			$slotsEmpty.hide().text('')
			updateNextButton()
		}

		function setSlotsMessage(text) {
			if (!text) {
				$slotsEmpty.hide().text('')
				return
			}
			$slotsEmpty.text(text).show()
		}

		function currentParams() {
			const salonId = $form.attr('data-salon-id') || ''
			const serviceId = $form.attr('data-service-id') || ''
			const masterId = $form.attr('data-master-id') || ''
			return {salonId, serviceId, masterId}
		}

		async function refreshAvailableDates() {
			const params = currentParams()
			if (!params.serviceId || (!params.salonId && !params.masterId)) {
				availableDates = new Set()
				if (datepicker) datepicker.update({})
				return
			}

			const now = new Date()
			const from = formatYmd(now)
			const to = formatYmd(new Date(now.getFullYear(), now.getMonth(), now.getDate() + 14))
			let url = '/api/availability/dates/?from=' + encodeURIComponent(from) +
				'&to=' + encodeURIComponent(to) +
				'&service_id=' + encodeURIComponent(params.serviceId)
			if (params.salonId) {
				url += '&salon_id=' + encodeURIComponent(params.salonId)
			}
			if (params.masterId) {
				url += '&master_id=' + encodeURIComponent(params.masterId)
			}

			try {
				const payload = await fetchJson(url)
				const dates = (payload && payload.dates) || []
				availableDates = new Set(dates)
			} catch (e) {
				availableDates = new Set()
			}

			if (datepicker) {
				datepicker.update({})
			}

			const selected = $form.attr('data-date') || ''
			if (selected && availableDates.size && !availableDates.has(selected)) {
				$form.attr('data-date', '')
				clearSlots()
			}

			if (!($form.attr('data-date') || '') && availableDates.size) {
				const first = Array.from(availableDates)[0]
				const asDate = parseYmd(first)
				if (asDate && datepicker) {
					datepicker.selectDate(asDate)
				}
			}
		}

			async function loadSlotsForSelectedDate() {
				const params = currentParams()
				const date = $form.attr('data-date') || ''
				if (!params.serviceId || !date || !params.salonId) {
					clearSlots()
					return
				}

			clearSlots()
			setSlotsMessage('Загрузка...')

			let url = '/api/availability/slots/?date=' + encodeURIComponent(date) +
				'&salon_id=' + encodeURIComponent(params.salonId) +
				'&service_id=' + encodeURIComponent(params.serviceId)
			if (params.masterId) {
				url += '&master_id=' + encodeURIComponent(params.masterId)
			}

				let slots = []
				try {
					const payload = await fetchJson(url)
					slots = (payload && payload.slots) || []
				} catch (e) {
					slots = []
				}

				if (!Array.isArray(slots) || !slots.length) {
					setSlotsMessage('Нет свободных окон на выбранную дату')
					return
				}
				setSlotsMessage('')

				const todayYmd = formatYmd(new Date())
				const isToday = date === todayYmd
				const nowMs = Date.now()
				let hasEnabledSlots = false

				slots.forEach(function(slot) {
					const startsAt = String(slot.starts_at || '')
					const timeStr = startsAt.slice(11, 16)
					const hour = Number(timeStr.slice(0, 2))
					const startMs = Date.parse(startsAt)
					const isPastSlot = isToday && !Number.isNaN(startMs) && startMs <= nowMs
					const apiAvailable = slot && slot.is_available !== false
					const isDisabled = isPastSlot || !apiAvailable

					const $btn = $('<button/>', {
						'class': 'time__elems_btn',
						'data-starts-at': startsAt,
						'data-time': timeStr,
						'text': timeStr,
					})
					if (isDisabled) {
						$btn.prop('disabled', true)
						$btn.attr('aria-disabled', 'true')
					} else {
						hasEnabledSlots = true
					}
					if (hour < 12) $slotsMorning.append($btn)
					else if (hour < 17) $slotsDay.append($btn)
					else $slotsEvening.append($btn)
				})

				if (!hasEnabledSlots) {
					setSlotsMessage('Нет свободных окон на выбранную дату')
				}
			}

		if (document.querySelector('#datepickerHere')) {
			datepicker = new AirDatepicker('#datepickerHere', {
				onSelect: function(args) {
					if (!args || !args.date) return
					const ymd = formatYmd(args.date)
					$form.attr('data-date', ymd)
					clearSlots()
					loadSlotsForSelectedDate()
				},
				onRenderCell: function(args) {
					if (!args || args.cellType !== 'day') return
					if (!availableDates || !availableDates.size) return
					const ymd = formatYmd(args.date)
					if (!availableDates.has(ymd)) {
						return {disabled: true}
					}
				},
			})
		}

		$salonPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Загрузка...</div></div>')
		try {
			const salonsPayload = await fetchJson('/api/salons/')
			$salonPanel.html(renderSalons(salonsPayload && salonsPayload.results))
		} catch (e) {
			$salonPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Не удалось загрузить салоны</div></div>')
		}

			async function loadSalonCatalog(salonId) {
				const payloads = await Promise.all([
					fetchJson('/api/salons/' + encodeURIComponent(salonId) + '/services/'),
					fetchJson('/api/salons/' + encodeURIComponent(salonId) + '/masters/'),
				])
				$servicesPanel.html(renderServicesByCategories(payloads[0]))
				$mastersPanel.html(renderMasters(payloads[1] && payloads[1].results))
			}

			$(document).on('click', '.service__salons > .panel .accordion__block', async function(e) {
				e.preventDefault()

				const $row = $(this)
				if ($row.attr('data-action') === 'master-first') {
					$form.attr('data-flow', 'master-first')
					$form.attr('data-salon-id', '')
					$form.attr('data-service-id', '')
					$form.attr('data-master-id', '')
					$form.attr('data-date', '')
					$form.attr('data-time', '')
					$form.attr('data-starts-at', '')

					resetServiceSelection()
					resetMasterSelection()
					clearSlots()

					const $salonButton = $row.closest('.service__salons').find('> button.accordion')
					$salonButton.addClass('selected').text('Любой салон')
					closeAccordion($salonButton)

					$servicesPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Сначала выберите мастера</div></div>')
					$mastersPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Загрузка...</div></div>')
					try {
						const mastersPayload = await fetchJson('/api/masters/')
						$mastersPanel.html(renderMastersGlobal(mastersPayload && mastersPayload.results))
					} catch (err) {
						$mastersPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Не удалось загрузить мастеров</div></div>')
					}

					updateNextButton()
					return
				}

				const salonId = $row.attr('data-salon-id')
				const name = $row.find('> .accordion__block_intro').text()
				const address = $row.find('> .accordion__block_address').text()

				const $salonButton = $row.closest('.service__salons').find('> button.accordion')
			$salonButton.addClass('selected').text(name + (address ? '  ' + address : ''))
			closeAccordion($salonButton)

				$form.attr('data-flow', 'salon-first')
				$form.attr('data-salon-id', salonId || '')
				$form.attr('data-service-id', '')
				$form.attr('data-master-id', '')
				$form.attr('data-date', '')
				$form.attr('data-time', '')
				$form.attr('data-starts-at', '')

				resetServiceSelection()
				resetMasterSelection()
				clearSlots()

				$servicesPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Загрузка...</div></div>')
				$mastersPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Загрузка...</div></div>')

				try {
					await loadSalonCatalog(salonId)
				} catch (err) {
					$servicesPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Не удалось загрузить услуги</div></div>')
					$mastersPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Не удалось загрузить мастеров</div></div>')
				}

				await refreshAvailableDates()
				updateNextButton()
			})

			$(document).on('click', '.service__services > .panel .accordion__block_item', async function(e) {
				e.preventDefault()

			const $item = $(this)
			const serviceId = $item.attr('data-service-id')
			const title = $item.find('> .accordion__block_item_intro').text()
			const price = $item.find('> .accordion__block_item_address').text()

			const $servicesButton = $item.closest('.service__services').find('> button.accordion')
			$servicesButton.addClass('selected').text(title + (price ? '  ' + price : ''))
			closeAccordion($servicesButton)

				$form.attr('data-service-id', serviceId || '')
				$form.attr('data-date', '')
				$form.attr('data-time', '')
				$form.attr('data-starts-at', '')
				clearSlots()
				await refreshAvailableDates()
				updateNextButton()
			})

			$(document).on('click', '.service__masters > .panel .accordion__block', async function(e) {
				e.preventDefault()

				const $row = $(this)
				const masterId = $row.attr('data-master-id')
				const primarySalonId = $row.attr('data-primary-salon-id')

				const $mastersButton = $row.closest('.service__masters').find('> button.accordion')
				$mastersButton.addClass('selected').html($row.clone())
				closeAccordion($mastersButton)

				$form.attr('data-master-id', masterId || '')
				$form.attr('data-date', '')
				$form.attr('data-time', '')
				$form.attr('data-starts-at', '')
				clearSlots()

				if (($form.attr('data-flow') || '') === 'master-first' && primarySalonId && !$form.attr('data-salon-id')) {
					$form.attr('data-salon-id', primarySalonId)
					const $salonButton = $('.service__salons').find('> button.accordion')
					$salonButton.addClass('selected').text($row.find('.accordion__block_prof').text() || 'Салон')

					$servicesPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Загрузка...</div></div>')
					try {
						await loadSalonCatalog(primarySalonId)
					} catch (err) {
						$servicesPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Не удалось загрузить услуги</div></div>')
					}
				}

				await refreshAvailableDates()
				updateNextButton()
			})

					$(document).on('click', '.time__elems_btn', function(e) {
						e.preventDefault()
						if ($(this).prop('disabled')) {
							return
						}
						$('.time__elems_btn').removeClass('active')
						$(this).addClass('active')
						const startsAt = $(this).attr('data-starts-at') || ''
						const timeStr = $(this).attr('data-time') || ''
						$form.attr('data-starts-at', startsAt)
					$form.attr('data-time', timeStr)
					updateNextButton()
				})

				async function prefillFromQuery() {
					if (!preSalonId) return

					const $salonRow = $('.service__salons > .panel .accordion__block[data-salon-id="' + preSalonId + '"]')
					if (!$salonRow.length) return

					const name = $salonRow.find('> .accordion__block_intro').text()
					const address = $salonRow.find('> .accordion__block_address').text()

					const $salonButton = $('.service__salons').find('> button.accordion')
					$salonButton.addClass('selected').text(name + (address ? '  ' + address : ''))
					closeAccordion($salonButton)

					$form.attr('data-flow', 'salon-first')
					$form.attr('data-salon-id', preSalonId)
					$form.attr('data-service-id', '')
					$form.attr('data-master-id', '')
					$form.attr('data-date', '')
					$form.attr('data-time', '')
					$form.attr('data-starts-at', '')

					resetServiceSelection()
					resetMasterSelection()
					clearSlots()

					$servicesPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Загрузка...</div></div>')
					$mastersPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Загрузка...</div></div>')

					try {
						await loadSalonCatalog(preSalonId)
					} catch (err) {
						$servicesPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Не удалось загрузить услуги</div></div>')
						$mastersPanel.html('<div class="accordion__block fic"><div class="accordion__block_intro">Не удалось загрузить мастеров</div></div>')
						return
					}

					await refreshAvailableDates()

					if (!preMasterId) return
					const $masterRow = $('.service__masters > .panel .accordion__block[data-master-id="' + preMasterId + '"]')
					if (!$masterRow.length) return

					const $mastersButton = $('.service__masters').find('> button.accordion')
					$mastersButton.addClass('selected').html($masterRow.clone())
					closeAccordion($mastersButton)

					$form.attr('data-master-id', preMasterId)
					$form.attr('data-date', '')
					$form.attr('data-time', '')
					$form.attr('data-starts-at', '')
					clearSlots()

					await refreshAvailableDates()
				}

				await prefillFromQuery()
				updateNextButton()
			}

		initServiceCatalog()

		function isServiceConfirmPage() {
			return $('.serviceFinallyPage').length && $('.serviceFinally__form').length
		}

		function getQueryParam(name) {
			try {
				const url = new URL(window.location.href)
				return url.searchParams.get(name)
			} catch (e) {
				return null
			}
		}

		function formatDateRu(ymd) {
			const parts = String(ymd || '').split('-')
			if (parts.length !== 3) return ymd
			return parts[2] + '.' + parts[1] + '.' + parts[0]
		}

		async function initServiceConfirm() {
			if (!isServiceConfirmPage()) return
			try { await ensureCsrf() } catch (e) {}

			const holdId = getQueryParam('hold_id')
			const $form = $('.serviceFinally__form')
			const $error = $('[data-role="booking-error"]')
			const $success = $('[data-role="booking-success"]')
			const $holdInput = $form.find('input[name="hold_id"]')

			function showError(text) {
				$success.hide().text('')
				$error.text(text || '').show()
			}
			function showSuccess(text) {
				$error.hide().text('')
				$success.text(text || '').show()
			}

			if (!holdId) {
				showError('Не найдена бронь. Вернитесь на страницу выбора услуги.')
				return
			}

			$holdInput.val(holdId)

			async function loadHold() {
				const payload = await apiGet('/api/booking/holds/' + encodeURIComponent(holdId) + '/')
				const summary = payload && payload.summary
				if (!summary) {
					throw new Error('invalid_response')
				}

				$('[data-role="salon-name"]').text((summary.salon && summary.salon.name) || '—')
				$('[data-role="salon-address"]').text((summary.salon && summary.salon.address) || '—')
				$('[data-role="service-title"]').text((summary.service && summary.service.title) || '—')
				$('[data-role="total-price"]').text(formatRuble(summary.total_price))

				const startsAt = String(summary.starts_at || '')
				const timeStr = startsAt.slice(11, 16)
				const dateStr = startsAt.slice(0, 10)
				$('[data-role="starts-time"]').text(timeStr || '—')
				$('[data-role="starts-date"]').text(formatDateRu(dateStr) || '—')

				if (summary.master) {
					$('[data-role="master-name"]').text(summary.master.name || '—')
					const imgUrl = summary.master.image_url ? String(summary.master.image_url) : staticPath('img/masters/avatar/vizajist1.svg')
					$('[data-role="master-avatar"]').attr('src', imgUrl)
				} else {
					$('[data-role="master-name"]').text('Любой мастер')
					$('[data-role="master-avatar"]').attr('src', staticPath('img/masters/avatar/all.svg'))
				}

				return summary
			}

			try {
				await loadHold()
			} catch (err) {
				showError('Не удалось загрузить бронь. Возможно, она истекла.')
				return
			}

			$form.on('click', '[data-action="apply-promo"]', async function(e) {
				e.preventDefault()
				const code = String($form.find('input[name="promo"]').val() || '').trim()
				if (!code) {
					showError('Введите промокод.')
					return
				}
				try {
					await apiPost('/api/booking/holds/' + encodeURIComponent(holdId) + '/apply-promo/', {promo_code: code})
					await loadHold()
					showSuccess('Промокод применён.')
				} catch (err) {
					showError('Промокод не найден или неактивен.')
				}
			})

			$form.on('click', '[data-action="back"]', function(e) {
				e.preventDefault()
				window.history.back()
			})

			$form.on('submit', async function(e) {
				e.preventDefault()
				$error.hide().text('')
				$success.hide().text('')

				const name = String($form.find('input[name="fname"]').val() || '').trim()
				const phone = String($form.find('input[name="tel"]').val() || '').trim()
				const comment = String($form.find('textarea[name="contactsTextarea"]').val() || '').trim()
				const consentChecked = $form.find('input.contacts__form_checkbox').is(':checked')

				if (!phone) {
					showError('Введите номер телефона.')
					return
				}
				if (!consentChecked) {
					showError('Нужно согласие на обработку персональных данных.')
					return
				}

				try {
					const res = await apiPost('/api/appointments/', {
						hold_id: holdId,
						phone: phone,
						name: name,
						comment: comment,
						pd_consent: true,
					})
					if (res && res.appointment_id) {
						alert('Вы успешно записаны. Номер записи №' + res.appointment_id + '.')
						window.location.href = '/service/'
					} else {
						showError('Не удалось создать запись.')
					}
				} catch (err) {
					showError('Не удалось создать запись. Попробуйте выбрать другое время.')
				}
			})
		}

		initServiceConfirm()
		$(document).on('click', '.servicePage', function() {
			updateNextButton()
		})
			//popup
			$(document).on('click', '[data-action="auth-open"]', function(e) {
				e.preventDefault()
				$('#authModal').arcticmodal();
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
			// service booking: Next -> create hold -> open confirm page
			$('.time__btns_next').click(async function(e) {
			if (!isServicePage()) return
			e.preventDefault()

			if (!$(this).hasClass('active')) {
				return
			}

			try { await ensureCsrf() } catch (err) {}

			const $form = $('.service__form')
			const salonId = $form.attr('data-salon-id') || ''
			const serviceId = $form.attr('data-service-id') || ''
			const masterId = $form.attr('data-master-id') || ''
			const startsAt = $form.attr('data-starts-at') || ''

			if (!salonId || !serviceId || !startsAt) {
				return
			}

			const payload = {
				salon_id: Number(salonId),
				service_id: Number(serviceId),
				starts_at: startsAt,
			}
			if (masterId) {
				payload.master_id = Number(masterId)
			}

				try {
					const res = await apiPost('/api/booking/holds/', payload)
					if (res && res.hold_id) {
						window.location.href = '/service/confirm/?hold_id=' + encodeURIComponent(res.hold_id)
					}
				} catch (err) {
					const code = err && err.message
					if (code === 'invalid_starts_at') {
						alert('Нельзя записаться на прошедшее время. Выберите другое время.')
						return
					}
					if (code === 'slot_unavailable') {
						const $selected = $('.time__elems_btn.active')
						$selected.removeClass('active').prop('disabled', true).attr('aria-disabled', 'true')

						$form.attr('data-time', '')
						$form.attr('data-starts-at', '')
						updateNextButton()

						alert('Этот слот уже занят. Выберите другое время.')
						return
					}
					alert('Не удалось забронировать слот. Попробуйте выбрать другое время.')
				}
			})

		$('.time__btns_home').click(function(e) {
			if (!isServicePage()) return
			e.preventDefault()
			window.location.href = '/'
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
