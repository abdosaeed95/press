<template>
	<div class="flex items-center space-x-1">
		<FormControl
			class="w-52"
			:label="label ? label : 'Date'"
			type="select"
			variant="outline"
			:options="dayOptions"
			v-model="scheduledDate"
		/>
		<FormControl
			class="w-24"
			:class="label ? 'mt-5' : ''"
			:label="label ? '' : 'Hour'"
			type="select"
			variant="outline"
			:options="hourOptions"
			v-model="scheduledHour"
		/>
		<FormControl
			class="w-24"
			:class="label ? 'mt-5' : ''"
			:label="label ? '' : 'Minute'"
			type="select"
			variant="outline"
			:options="minuteOptions"
			v-model="scheduledMinute"
		/>
	</div>
</template>

<script>
import { dayjsCairo } from '../utils/dayjs';

export default {
	props: ['modelValue', 'label', 'minimumTime'],
	emits: ['update:modelValue'],
	computed: {
		scheduledDate: {
			get() {
				return this.modelValue ? this.modelValue.split('T')[0] : '';
			},
			set(value) {
				this.$emit(
					'update:modelValue',
					`${value}T${this.scheduledHour}:${this.scheduledMinute}`
				);
			},
		},
		scheduledHour: {
			get() {
				return this.modelValue
					? Number(this.modelValue.split('T')[1].split(':')[0])
					: '';
			},
			set(value) {
				this.$emit(
					'update:modelValue',
					`${this.scheduledDate}T${String(value).padStart(2, '0')}:${String(
						this.scheduledMinute
					).padStart(2, '0')}`
				);
			},
		},
		scheduledMinute: {
			get() {
				return this.modelValue
					? Number(this.modelValue.split('T')[1].split(':')[1])
					: '';
			},
			set(value) {
				this.$emit(
					'update:modelValue',
					`${this.scheduledDate}T${String(this.scheduledHour).padStart(
						2,
						'0'
					)}:${String(value).padStart(2, '0')}`
				);
			},
		},
		dayOptions() {
			const firstDay =
				this.minimumTime && dayjsCairo(this.minimumTime).isAfter(dayjsCairo())
					? dayjsCairo(this.minimumTime)
					: dayjsCairo();
			let days = [];
			for (let i = 0; i < 7; i++) {
				days.push({
					label: firstDay.add(i, 'day').format('dddd, MMMM D'),
					value: firstDay.add(i, 'day').format('YYYY-MM-DD'),
				});
			}
			return days;
		},
		hourOptions() {
			let options = [...Array(24).keys()].map((n) => ({
				label:
					n < 12
						? `${(n == 0 ? 12 : n).toString().padStart(2, '0')} AM`
						: `${(n != 12 ? n - 12 : n).toString().padStart(2, '0')} PM`,
				value: n,
			}));

			const now = dayjsCairo();
			if (this.scheduledDate === now.format('YYYY-MM-DD')) {
				options = options.filter(
					(option) =>
						option.value >= (now.minute() < 45 ? now.hour() : now.hour() + 1)
				);
			}
			if (
				this.minimumTime &&
				this.scheduledDate === dayjsCairo(this.minimumTime).format('YYYY-MM-DD')
			) {
				const minimumTime = dayjsCairo(this.minimumTime);
				options = options.filter(
					(option) =>
						option.value >=
						(minimumTime.minute() < 45
							? minimumTime.hour()
							: minimumTime.hour() + 1)
				);
			}

			return options;
		},
		minuteOptions() {
			const now = dayjsCairo();
			let options = [0, 15, 30, 45].map((i) => ({
				label: i.toString().padStart(2, '0'),
				value: i,
			}));

			if (
				this.scheduledDate === now.format('YYYY-MM-DD') &&
				Number(this.scheduledHour) === now.hour()
			) {
				options = options.filter((option) => option.value >= now.minute());
			}
			if (
				this.minimumTime &&
				this.scheduledDate ===
					dayjsCairo(this.minimumTime).format('YYYY-MM-DD') &&
				Number(this.scheduledHour) === dayjsCairo(this.minimumTime).hour()
			) {
				options = options.filter(
					(option) => option.value > dayjsCairo(this.minimumTime).minute()
				);
			}

			return options;
		},
	},
};
</script>
