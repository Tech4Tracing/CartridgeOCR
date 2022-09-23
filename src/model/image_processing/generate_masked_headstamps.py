import numpy as np
import cv2
import json

class GenerateMasks:
    def __init__(self, extracted_headstamps_file_path: str, output_file_path: str):
        self.extracted_headstamps_file_path = extracted_headstamps_file_path
        self.output_file_path = output_file_path

        self.detection_data = None
        self.images = []
        self.masked_images = []

    def load_detections_json(self):
        with open(f"{self.extracted_headstamps_file_path}/detections.json") as f:
            self.detection_data = json.load(f)

    def load_images_to_process(self):
        for d in self.detection_data["all_detections"]:
            file_name = d["filename"].split("/")[-1]
            
            for indexer, detection in enumerate(d["detections"]):
                image_file_name = file_name + f"_{indexer}.png"
                casing_box = np.array(detection["casing"]["box"])
                primer_box = np.array(detection["primer"]["box"])
                self.images.append([image_file_name, casing_box, primer_box])

    def read_image(self, image_file_name: str) -> np.ndarray:
        im = cv2.imread(f"{self.extracted_headstamps_file_path}/{image_file_name}")
        return im

    def get_bounding_box_center_and_radius(self, image_shape: np.ndarray, box: np.ndarray) -> tuple:
        x0, x1 = np.round((box[::2] * image_shape[1])).astype("int")
        y0, y1 = np.round((box[1::2] * image_shape[0])).astype("int")

        mid_x = x0 + (x1 - x0) / 2
        mid_y = y0 + (y1 - y0) / 2
        center = (int(mid_x), int(mid_y))

        radius = int(max((x1 - x0) / 2, (y1 - y0) / 2))

        return (center, radius)

    def create_mask(self, image_shape: np.ndarray, center, radius: int) -> np.ndarray:
        mask = np.zeros(image_shape).astype("uint8")
        cv2.circle(mask, center, radius, (255, 255, 255), -1)

        return mask

    def apply_mask_to_image(self, im: np.ndarray, casing_mask: np.ndarray, primer_mask: np.ndarray) -> np.ndarray:
        masked_im = im.copy()
        headstamp_mask = cv2.subtract(casing_mask, primer_mask)
        masked_im[headstamp_mask != 255] = 255

        return masked_im

    def write_image(self, image_file_name: str, im: np.ndarray):
        cv2.imwrite(f"{self.output_file_path}/masked_{image_file_name}", im)

    def process_images(self):
        self.load_detections_json()
        self.load_images_to_process()

        for image_name, casing_box, primer_box in self.images:
            img = self.read_image(image_name)

            casing_center, casing_radius = self.get_bounding_box_center_and_radius(img.shape, casing_box)
            primer_center, primer_radius = self.get_bounding_box_center_and_radius(img.shape, primer_box)

            casing_mask = self.create_mask(img.shape, casing_center, casing_radius)
            primer_mask = self.create_mask(img.shape, primer_center, primer_radius)

            masked_img = self.apply_mask_to_image(img, casing_mask, primer_mask)

            self.write_image(image_name, masked_img)


if __name__ == "__main__":
    import_path = "./src/model/image_processing/extracted_headstamps"
    export_path = "./src/model/image_processing/masked_extracted_headstamps"

    gm = GenerateMasks(import_path, export_path)
    gm.process_images()
