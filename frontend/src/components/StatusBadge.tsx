import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const normalized = status.toLowerCase();
  let badgeClass = 'badge-draft';

  if (['pending'].includes(normalized)) badgeClass = 'badge-pending';
  else if (['approved', 'completed', 'published'].includes(normalized)) badgeClass = 'badge-approved';
  else if (['rejected', 'failed'].includes(normalized)) badgeClass = 'badge-rejected';
  else if (['running'].includes(normalized)) badgeClass = 'badge-running';
  else if (['unpublished'].includes(normalized)) badgeClass = 'badge-unpublished';

  return (
    <span className={`badge ${badgeClass}`}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor' }} />
      {status}
    </span>
  );
};
