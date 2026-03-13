import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/ru';

dayjs.extend(relativeTime);
dayjs.locale('ru');

export function formatDate(date: string | null | undefined): string {
  if (!date) return '-';
  return dayjs(date).format('DD.MM.YYYY HH:mm:ss');
}

export function formatDateShort(date: string | null | undefined): string {
  if (!date) return '-';
  return dayjs(date).format('DD.MM HH:mm');
}

export function formatRelative(date: string | null | undefined): string {
  if (!date) return '-';
  return dayjs(date).fromNow();
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export function formatNumber(value: number | null | undefined, decimals = 2): string {
  if (value == null) return '-';
  return value.toFixed(decimals);
}
