<template>
	<div>
		<div class="mb-3">
			<div>
				<h2 class="mt-6 space-y-1 text-lg font-semibold">
					Enter the Application Server Details
				</h2>
				<div class="mt-6 flex flex-col gap-4">
					<p class="text-black-900 text-base">Public IP of the Server</p>
					<FormControl
						class="z-10 w-full rounded-r-none"
						:value="appPublicIP"
						@change="$emit('update:appPublicIP', $event.target.value)"
					/>
					<ErrorMessage class="text-sm" :message="publicIpErrorMessage" />

					<p class="text-black-900 text-base">Private IP of the Server</p>
					<FormControl
						class="z-10 w-full rounded-r-none"
						:value="appPrivateIP"
						@change="$emit('update:appPrivateIP', $event.target.value)"
					/>
					<ErrorMessage class="text-sm" :message="privateIpErrorMessage" />
				</div>

				<h2 class="mt-8 space-y-1 text-lg font-semibold">
					Enter the DB Server Details
				</h2>
				<div class="mt-6 flex flex-col gap-4">
					<p class="text-black-900 text-base">Public IP of the DB Server</p>
					<FormControl
						class="z-10 w-full rounded-r-none"
						:value="dbPublicIP"
						@change="$emit('update:dbPublicIP', $event.target.value)"
					/>
					<ErrorMessage class="text-sm" :message="dbPublicIpErrorMessage" />

					<p class="text-black-900 text-base">Private IP of the DB Server</p>
					<FormControl
						class="z-10 w-full rounded-r-none"
						:value="dbPrivateIP"
						@change="$emit('update:dbPrivateIP', $event.target.value)"
					/>
					<ErrorMessage class="text-sm" :message="dbPrivateIpErrorMessage" />
				</div>

				<h2 class="mt-8 space-y-1 text-lg font-semibold">
					Cloudflare Connection
				</h2>
				<div class="mt-6 flex flex-col gap-4">
					<FormControl
						type="checkbox"
						label="Route server management through Cloudflare"
						:modelValue="behindCloudflare"
						@update:modelValue="$emit('update:behindCloudflare', $event)"
						:disabled="cloudflareZones.length === 0"
					/>
					<FormControl
						v-if="behindCloudflare"
						type="select"
						label="Cloudflare Zone"
						:options="cloudflareZones"
						:modelValue="cloudflareZone"
						@update:modelValue="$emit('update:cloudflareZone', $event)"
					/>
					<p v-if="behindCloudflare" class="text-sm text-gray-600">
						The public IP is used only for the initial tunnel bootstrap. Press
						uses the tunnel after it becomes healthy.
					</p>
				</div>
			</div>
		</div>
	</div>
</template>
<script>
export default {
	name: 'SelfHostedServerForm',
	props: [
		'appPublicIP',
		'appPrivateIP',
		'dbPublicIP',
		'dbPrivateIP',
		'behindCloudflare',
		'cloudflareZone',
		'cloudflareZones',
		'error',
	],
	emits: [
		'update:appPublicIP',
		'update:appPrivateIP',
		'update:dbPublicIP',
		'update:dbPrivateIP',
		'update:behindCloudflare',
		'update:cloudflareZone',
		'update:error',
	],
	watch: {
		hasError() {
			this.$emit('update:error', this.hasError);
		},
	},
	mounted() {
		this.$emit('update:error', this.hasError);
	},
	computed: {
		publicIpErrorMessage() {
			return this.validateIP(this.appPublicIP, 'Public');
		},
		dbPublicIpErrorMessage() {
			return this.validateIP(this.dbPublicIP, 'DB Public');
		},
		privateIpErrorMessage() {
			return this.validateIP(this.appPrivateIP, 'Private');
		},
		dbPrivateIpErrorMessage() {
			return this.validateIP(this.dbPrivateIP, 'DB Private');
		},
		hasError() {
			return (
				this.publicIpErrorMessage !== null ||
				this.privateIpErrorMessage !== null ||
				this.dbPublicIpErrorMessage !== null ||
				this.dbPrivateIpErrorMessage !== null
			);
		},
	},
	methods: {
		validateIP(ip, type) {
			try {
				const stripped_ip = ip.replace(/\s+/g, '');
				const ipAddressRegex = /^([0-9]{1,3}\.){3}[0-9]{1,3}$/;
				const ver = ipAddressRegex.test(stripped_ip);
				return ver ? null : `${type} IP is invalid`;
			} catch {
				return `${type} IP cannot be blank`;
			}
		},
	},
};
</script>
