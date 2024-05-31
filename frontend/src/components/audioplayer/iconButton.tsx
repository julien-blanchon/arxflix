import React from 'react';
import cn from 'classnames';

type Intent = 'primary' | 'secondary';
type Size = 'sm' | 'md' | 'lg';

interface IconButtonProps extends React.ComponentPropsWithoutRef<'button'> {
  intent?: Intent; // can add more
  size?: Size;
}

const colorMap: Record<Intent, string> = {
  primary: 'bg-primary text-white',
  secondary: 'bg-white text-slate-400',
};

const sizeMap: Record<Size, string> = {
  sm: 'h-8 w-8',
  md: 'h-10 w-10',
  lg: 'h-12 w-12',
};

export default function IconButton({
  intent = 'primary',
  size = 'md',
  className,
  ...props
}: IconButtonProps) {
  const colorClass = colorMap[intent];
  const sizeClass = sizeMap[size];
  const classes = cn(
    'rounded-full flex items-center justify-center ring-offset-primary focus:outline-none focus:ring-2 focus:ring-amber-600 focus:ring-offset-2 disabled:opacity-60',
    colorClass,
    sizeClass,
    className
  );
  return <button className={classes} {...props} />;
}
