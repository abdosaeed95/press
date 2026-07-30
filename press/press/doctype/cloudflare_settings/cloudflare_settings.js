// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cloudflare Settings', {
	refresh(frm) {
		if (!frm.doc.account_id) {
			frm.add_custom_button(
				__('Discover Accounts'),
				() => show_account_dialog(frm),
				__('Cloudflare'),
			);
		}
		if (frm.is_new() || !frm.doc.enabled) {
			return;
		}

		frm.add_custom_button(
			__('Test Connection'),
			async () => {
				const { message } = await frm.call('test_connection');
				frappe.msgprint(
					__('Connected to {0}. {1} zone(s) are accessible.', [
						message.account.name,
						message.zones,
					])
				);
				frm.reload_doc();
			},
			__('Cloudflare')
		);

		frm.add_custom_button(
			__('Import Zone'),
			() => show_zone_dialog(frm),
			__('Cloudflare')
		);

		if (frm.doc.registrar_enabled) {
			frm.add_custom_button(
				__('Search Available Domains'),
				() => show_domain_search(frm),
				__('Cloudflare')
			);
		}

		if (frm.doc.manage_access) {
			frm.add_custom_button(
				__('Rotate Access Service Token'),
				() =>
					frappe.confirm(
						__('Rotate the Access service token used by Press?'),
						() =>
							frm
								.call('rotate_access_service_token')
								.then(() => frappe.show_alert(__('Access token rotated.')))
					),
				__('Cloudflare')
			);
		}
	},
});

async function show_account_dialog(frm) {
	if (!frm.doc.api_token || frm.doc.api_token === '********') {
		frappe.throw(__('Enter a new Cloudflare API token first.'));
	}
	const { message: accounts } = await frappe.call({
		method:
			'press.press.doctype.cloudflare_settings.cloudflare_settings.discover_accounts',
		args: { api_token: frm.doc.api_token },
	});
	const dialog = new frappe.ui.Dialog({
		title: __('Select Cloudflare Account'),
		fields: [
			{
				fieldname: 'account',
				fieldtype: 'Select',
				label: __('Account'),
				options: accounts.map(
					(account) => `${account.name} (${account.id})`,
				),
				reqd: 1,
			},
		],
		primary_action_label: __('Select'),
		primary_action: ({ account: selected_account }) => {
			const account = accounts.find(
				(value) => `${value.name} (${value.id})` === selected_account,
			);
			frm.set_value('account_id', account.id);
			frm.set_value('account_name', account.name);
			dialog.hide();
		},
	});
	dialog.show();
}

async function show_zone_dialog(frm) {
	const { message: zones } = await frm.call('get_zones');
	const dialog = new frappe.ui.Dialog({
		title: __('Import Cloudflare Zone'),
		fields: [
			{
				fieldname: 'domain',
				fieldtype: 'Select',
				label: __('Zone'),
				options: zones.map((zone) => zone.name),
				reqd: 1,
			},
			{
				fieldname: 'default_cluster',
				fieldtype: 'Link',
				label: __('Default Cluster'),
				options: 'Cluster',
				reqd: 1,
			},
		],
		primary_action_label: __('Import'),
		primary_action: async ({ domain, default_cluster }) => {
			await frm.call('import_zone', { domain, default_cluster });
			dialog.hide();
			frappe.show_alert(__('Cloudflare zone imported.'));
			frm.reload_doc();
		},
	});
	dialog.show();
}

function show_domain_search(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __('Search Available Domains'),
		fields: [
			{
				fieldname: 'query',
				fieldtype: 'Data',
				label: __('Name or keywords'),
				reqd: 1,
			},
			{
				fieldname: 'extensions',
				fieldtype: 'Data',
				label: __('Extensions'),
				description: __(
					'Optional comma-separated extensions, such as com, app, dev.'
				),
			},
			{
				fieldname: 'results',
				fieldtype: 'HTML',
			},
		],
		primary_action_label: __('Search'),
		primary_action: async ({ query, extensions }) => {
			const { message } = await frm.call('search_domains', {
				query,
				extensions: extensions
					? extensions.split(',').map((extension) => extension.trim())
					: [],
			});
			const rows = message
				.map(
					(domain) =>
						`<tr><td>${frappe.utils.escape_html(domain.name)}</td><td>${
							domain.registrable ? __('Available') : __('Unavailable')
						}</td><td>${frappe.utils.escape_html(
							domain.pricing
								? `${domain.pricing.registration_cost} ${domain.pricing.currency}`
								: domain.reason || ''
						)}</td><td>${
							domain.registrable
								? `<button class="btn btn-xs btn-primary register-domain" data-domain="${frappe.utils.escape_html(
										domain.name
								  )}">${__('Register')}</button>`
								: ''
						}</td></tr>`
				)
				.join('');
			dialog.fields_dict.results.$wrapper.html(
				`<table class="table table-bordered"><thead><tr><th>${__(
					'Domain'
				)}</th><th>${__('Status')}</th><th>${__(
					'Registration Price'
				)}</th><th></th></tr></thead><tbody>${rows}</tbody></table>`
			);
			dialog.fields_dict.results.$wrapper
				.find('.register-domain')
				.on('click', async (event) => {
					const domain = event.currentTarget.dataset.domain;
					const { message: checked } = await frm.call('check_domains', {
						domains: [domain],
					});
					const result = checked[0];
					if (!result || !result.registrable) {
						frappe.throw(__('Domain {0} is no longer available.', [domain]));
					}
					const price = result.pricing.registration_cost;
					const currency = result.pricing.currency;
					frappe.confirm(
						__('Register {0} for {1} {2}? This charge is non-refundable.', [
							domain,
							price,
							currency,
						]),
						async () => {
							await frm.call('register_domain', {
								domain,
								expected_price: price,
								expected_currency: currency,
								confirm_registration: 1,
							});
							frappe.msgprint(
								__('Domain registration started for {0}.', [domain])
							);
						}
					);
				});
		},
	});
	dialog.show();
}
