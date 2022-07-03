import sys
# TODO: this shouldn't be necessary.
sys.path += ['.', '..', '../..']
import os
import argparse
import inference
import base64
import json
import logging


def parse_boolean(value):
    value = value.lower()

    if value in ["true", "yes", "y", "1", "t"]:
        return True
    elif value in ["false", "no", "n", "0", "f"]:
        return False

    return False


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # TODO: a variety of output options- save images, only return boxes, etc
    parser = argparse.ArgumentParser()
    parser.add_argument('--modelfolder', default='.')
    parser.add_argument('--checkpoint', default='checkpoint.pth')
    parser.add_argument('--render_images', help='Whether predictions should be rendered', type=parse_boolean, default=False)
    parser.add_argument('--output_images', type=str, default=None, help='Optionally, where to dump rendered output images. Requires render_images=True')
    parser.add_argument('input_file_or_folder')
    parser.add_argument('output_json')

    args = parser.parse_args()
    inf = inference.Inference()
    inf.init(modelfolder=args.modelfolder, checkpoint=args.checkpoint)

    # load the image and base64 encode it.
    with open(args.output_json, 'w', encoding='utf-8') as outF:
        def process_image(path):
            logging.info('processing {}'.format(path))
            with open(path, 'rb') as inF:
                encoded = base64.b64encode(inF.read())
                result = inf.run(json.dumps({
                    'image': encoded.decode(),
                    'render': args.render_images
                    }))
                if not args.render_images:
                    del result['image']
                return result

        # TODO
        def is_image(path):
            return path.lower().endswith('.jpg')

        if os.path.isdir(args.input_file_or_folder):
            if args.render_images and args.output_images is not None:
                os.makedirs(args.output_images, exist_ok=True)
            folder = args.input_file_or_folder
            for f in os.listdir(folder):
                path = os.path.join(folder, f)
                if is_image(path):
                    result = process_image(path)
                    result['filename'] = path
                    outF.write(json.dumps(result) + '\n')
                    if 'error' in result:
                        logging.error(result['error'])
                        continue
                    if args.render_images and args.output_images is not None:
                        output_file = os.path.join(args.output_images, f)
                        if os.path.exists(output_file):
                            raise Exception('Output file {} already exists'.format(output_file))
                        with open(output_file, 'wb', ) as outIm:
                            outIm.write(base64.b64decode(result['image']))
        else:
            result = process_image(args.input_file_or_folder)
            outF.write(json.dumps(result) + '\n')
