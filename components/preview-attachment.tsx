import type { FileUIPart } from "ai";
import Image from "next/image";

import { LoaderIcon } from "./icons";

export const PreviewAttachment = ({
  attachment,
  isUploading = false,
}: {
  attachment: FileUIPart;
  isUploading?: boolean;
}) => {
  const { filename, url, mediaType } = attachment;
  const displayName = filename ?? "Attachment";

  return (
    <div className="flex flex-col gap-2">
      <div className="relative flex flex-col justify-center items-center bg-muted rounded-md w-20 aspect-video">
        {mediaType ? (
          mediaType.startsWith("image") ? (
            <Image
              key={url}
              src={url}
              alt={displayName}
              fill
              className="rounded-md object-cover"
            />
          ) : (
            <div className="" />
          )
        ) : (
          <div className="" />
        )}

        {isUploading && (
          <div className="absolute text-zinc-500 animate-spin">
            <LoaderIcon />
          </div>
        )}
      </div>
      <div className="max-w-16 text-zinc-500 text-xs truncate">
        {displayName}
      </div>
    </div>
  );
};
